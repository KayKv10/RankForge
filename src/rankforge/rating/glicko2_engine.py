# src/rankforge/glicko2_engine.py

"""
A from-scratch implementation of the Glicko-2 rating system.
The formulas and steps are bsaed on the paper by Dr. Mark Glickman:
https://www.glicko.net/glicko/glicko2.pdf
"""

import math
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from rankforge.db import models

# ===============================================
# == Glicko-2 Core Implementation
# ===============================================


@dataclass
class Glicko2Rating:
    """Represents a player's rating in the standard Glicko scale."""

    mu: float = 1500.0
    phi: float = 350.0
    sigma: float = 0.06


class Glicko2Engine:
    """Encapsulates the Glicko-2 calculation logic."""

    # The system constant, tau, constrains the change in volatility over time.
    # A typical value is between 0.3 and 1.2.
    def __init__(self, tau: float = 0.5):
        self._tau = tau
        self._glicko_scale_constant = 173.7178

    def rate(
        self,
        player_rating: Glicko2Rating,
        opponent_ratings_and_outcomes: list[tuple[Glicko2Rating, float]],
    ) -> Glicko2Rating:
        """
        Calculates a player's new rating based on a series of match outcomes.
        """
        # Step 1 & 2: Convert to Glicko-2 scale
        mu = (player_rating.mu - 1500) / self._glicko_scale_constant
        phi = player_rating.phi / self._glicko_scale_constant
        sigma = player_rating.sigma

        if not opponent_ratings_and_outcomes:
            # If the player didn't play, only RD changes (Step 8 in paper)
            new_phi_scaled = math.sqrt(phi**2 + sigma**2)
            new_phi = new_phi_scaled * self._glicko_scale_constant
            return Glicko2Rating(player_rating.mu, new_phi, player_rating.sigma)

        # Step 3: Compute the estimated variance of the player's rating
        v = self._compute_v(mu, opponent_ratings_and_outcomes)

        # Step 4: Compute the estimated improvement in rating
        delta = self._compute_delta(mu, v, opponent_ratings_and_outcomes)

        # Step 5: Determine the new volatility
        sigma_prime = self._compute_new_sigma(delta, phi, v, sigma)

        # Step 6: Update the rating deviation to the new pre-rating period value
        phi_star = math.sqrt(phi**2 + sigma_prime**2)

        # Step 7: Update the rating and rating deviation
        phi_prime = 1 / math.sqrt(1 / phi_star**2 + 1 / v)
        mu_prime = mu + phi_prime**2 * self._sum_g_phi_j(
            mu, opponent_ratings_and_outcomes
        )

        # Step 8: Convert back to the original Glicko scale
        mu_new = mu_prime * self._glicko_scale_constant + 1500
        phi_new = phi_prime * self._glicko_scale_constant

        return Glicko2Rating(mu=mu_new, phi=phi_new, sigma=sigma_prime)

    def _g(self, phi: float) -> float:
        """The g() function from the Glickman paper."""
        return 1 / math.sqrt(1 + 3 * phi**2 / math.pi**2)

    def _E(self, mu: float, mu_j: float, phi_j: float) -> float:
        """The E() function, expected outcome against one opponent."""
        return 1 / (1 + math.exp(-self._g(phi_j) * (mu - mu_j)))

    def _compute_v(
        self, mu: float, opponent_ratings: list[tuple[Glicko2Rating, float]]
    ) -> float:
        """Computes the estimated variance `v`."""
        v_inv = 0.0
        for opponent, _ in opponent_ratings:
            mu_j = (opponent.mu - 1500) / self._glicko_scale_constant
            phi_j = opponent.phi / self._glicko_scale_constant
            g_phi_j = self._g(phi_j)
            E = self._E(mu, mu_j, phi_j)
            v_inv += g_phi_j**2 * E * (1 - E)
        return 1 / v_inv if v_inv != 0 else 0

    def _sum_g_phi_j(
        self, mu: float, opponent_ratings: list[tuple[Glicko2Rating, float]]
    ) -> float:
        """Helper to compute a sum used in delta and mu' calculation."""
        total = 0.0
        for opponent, score in opponent_ratings:
            mu_j = (opponent.mu - 1500) / self._glicko_scale_constant
            phi_j = opponent.phi / self._glicko_scale_constant
            total += self._g(phi_j) * (score - self._E(mu, mu_j, phi_j))
        return total

    def _compute_delta(
        self,
        mu: float,
        v: float,
        opponent_ratings: list[tuple[Glicko2Rating, float]],
    ) -> float:
        """Computes the estimated improvement `delta`."""
        return v * self._sum_g_phi_j(mu, opponent_ratings)

    def _compute_new_sigma(
        self, delta: float, phi: float, v: float, sigma: float
    ) -> float:
        """
        Determines the new volatility `sigma'` using an iterative algorithm.
        This is the most complex step of the Glicko-2 calculation.
        """
        a = math.log(sigma**2)
        delta_sq = delta**2
        phi_sq = phi**2
        tau_sq = self._tau**2

        def f(x: float) -> float:
            ex = math.exp(x)
            return (
                ex * (delta_sq - phi_sq - v - ex) / (2 * (phi_sq + v + ex) ** 2)
                - (x - a) / tau_sq
            )

        # Bisection method to find the root of f(x)
        A = a
        if delta_sq > phi_sq + v:
            B = math.log(delta_sq - phi_sq - v)
        else:
            k = 1
            while f(a - k * self._tau) < 0:
                k += 1
            B = a - k * self._tau

        f_A = f(A)
        f_B = f(B)
        epsilon = 0.000001

        while abs(B - A) > epsilon:
            C = A + (A - B) * f_A / (f_B - f_A)
            f_C = f(C)
            if f_C * f_B < 0:
                A = B
                f_A = f_B
            else:
                f_A /= 2
            B = C
            f_B = f_C

        return math.exp(A / 2)


# ===============================================
# == RankForge Integration
# ===============================================


def _calculate_player_scores(match: models.Match) -> dict[int, float]:
    """
    Parses match outcomes and calculates a normalized score for each player.

    - Prioritizes win/loss results for binary outcomes.
    - For ranked games, normalizes score based on the number of competing
      entities (teams or individual players in an FFA).
    - Defaults to 0.5 (draw) if outcome is not recognized.

    Returns:
        A dictionary mapping player_id to their calculated score.
    """
    player_scores = {}

    # Check for simple win/loss first, as it's the most direct outcome
    has_win_loss = any(
        p.outcome.get("result") in ["win", "loss"] for p in match.participants
    )
    if has_win_loss:
        for p in match.participants:
            result = p.outcome.get("result")
            if result == "win":
                player_scores[p.player_id] = 1.0
            elif result == "loss":
                player_scores[p.player_id] = 0.0
            else:
                player_scores[p.player_id] = 0.5  # Draw or other
        return player_scores

    # If no win/loss, proceed with ranked logic
    # Determine the number of competing entities (teams or players)
    team_ids = {p.team_id for p in match.participants}
    num_competitors = len(team_ids)
    num_opponents = num_competitors - 1

    if num_opponents <= 0:  # Not a competitive match
        for p in match.participants:
            player_scores[p.player_id] = 0.5
            # TODO: Raise an error here
        return player_scores

    # Map team_id to its rank for easy lookup
    team_ranks = {p.team_id: p.outcome.get("rank") for p in match.participants}

    for p in match.participants:
        rank = team_ranks.get(p.team_id)

        if rank is not None and isinstance(rank, int):
            # Normalized score: (NumOpponents - (Rank - 1)) / NumOpponents
            score = (num_opponents - (rank - 1)) / float(num_opponents)
            player_scores[p.player_id] = score
        else:
            player_scores[p.player_id] = 0.5  # Default for missing/invalid rank

    return player_scores


async def update_ratings_for_match(db: AsyncSession, match: models.Match) -> None:
    """
    Updates player ratings for a completed match using the Glicko-2 implementation.
    """
    engine = Glicko2Engine()
    player_profiles = {}
    player_ratings = {}

    # 1. Fetch all profiles and create Glicko2Rating objects
    for p in match.participants:
        profile = await models.GameProfile.find_by_player_and_game(
            db, p.player_id, match.game_id
        )
        if not profile:
            continue
        player_profiles[p.player_id] = profile
        player_ratings[p.player_id] = Glicko2Rating(
            mu=profile.rating_info["rating"],
            phi=profile.rating_info["rd"],
            sigma=profile.rating_info["vol"],
        )

    # 2. Calculate a normalized performance score for each player from the match outcome
    player_scores = _calculate_player_scores(match)
    new_ratings = {}

    # 3. For each player, calculate their new rating
    for p1 in match.participants:
        opponents_data = []
        p1_score = player_scores[p1.player_id]

        for p2 in match.participants:
            if p1.team_id == p2.team_id:
                continue

            opponent_rating = player_ratings[p2.player_id]
            # In this model, the outcome against every opponent is the same,
            # reflecting the player's overall performance in the match.
            opponents_data.append((opponent_rating, p1_score))

        # Calculate the new rating
        current_rating = player_ratings[p1.player_id]
        new_ratings[p1.player_id] = engine.rate(current_rating, opponents_data)

    # 3. Persist the new ratings to the database
    for p in match.participants:
        player_id = p.player_id
        if player_id not in new_ratings:
            continue

        profile_to_update = player_profiles[player_id]
        updated_rating = new_ratings[player_id]

        old_rating_info = profile_to_update.rating_info.copy()
        new_rating_info = {
            "rating": round(updated_rating.mu, 2),
            "rd": round(updated_rating.phi, 2),
            "vol": round(updated_rating.sigma, 6),
        }

        rating_change = {
            "rating_change": new_rating_info["rating"] - old_rating_info["rating"],
            "rd_change": new_rating_info["rd"] - old_rating_info["rd"],
            "vol_change": new_rating_info["vol"] - old_rating_info["vol"],
        }

        profile_to_update.rating_info = new_rating_info
        p.rating_info_change = rating_change
        db.add(profile_to_update)
        db.add(p)

    await db.commit()
