"""Scene 4: Token Manifold Collapse in LLM Generation.

Visualizes:
  1. Unconstrained candidate universe: 5x5x5 lattice cloud of 125 candidate points in {-2,-1,0,1,2}^3.
  2. Anti-morphism interior operators P_p(A) = {x in A : p(x)}:
     - PIN: Codepoint / alphabet filter
     - SHAPE: Grammatical arity filter
     - LAND_ON_ZERO(Phi_1): Cycle consistency filter
  3. Manifold reduction: 125 -> 19 (RESIDUAL state).
  4. Adaptive DEMAND: Host injects prefix constraint (1, -1) -> 1 (LANDED witness: (1, -1, 0)).
  5. Contrast path: Contradictory demand -> fixpoint 0 (REFUSED_EMPTY honest refusal).

Render sample frame:
    manim -qm -s scenes/scene4_token_manifold_collapse.py TokenManifoldCollapse

AuthorityEffect: None.
Claim Hygiene: Toy lattice model; demonstrates antimorphism interior operators from bench/packets/antimorphism.py.
"""

from __future__ import annotations

import itertools

from manim import (
    DOWN,
    RIGHT,
    UP,
    Dot,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    RoundedRectangle,
    Scene,
    Text,
    VGroup,
    config,
)

# 3Blue1Brown Theme Colors
BG_COLOR = "#0f111a"
COLOR_BLUE = "#3498db"
COLOR_TEAL = "#1abc9c"
COLOR_YELLOW = "#f1c40f"
COLOR_RED = "#e74c3c"
COLOR_GREEN = "#2ecc71"
COLOR_WHITE = "#f8f9fa"
COLOR_MUTED = "#7f8c8d"
COLOR_CARD = "#1a1d2e"
COLOR_PURPLE = "#9b59b6"

config.background_color = BG_COLOR


class TokenManifoldCollapse(Scene):
    """Main animation scene for Scene 4: Token Manifold Collapse in LLM Generation."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------------------
        # Act I: The Unconstrained Token Cloud (0:00 - 0:25)
        # ---------------------------------------------------------------------
        title = Text("Token Manifold Collapse", font_size=38, color=COLOR_WHITE, weight="BOLD")
        subtitle = Text(
            "Lattice Filtering via Anti-Morphism Operators", font_size=22, color=COLOR_BLUE
        )
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.15).to_edge(UP, buff=0.4)
        self.play(FadeIn(title_group), run_time=1.0)
        self.wait(0.5)

        # Generate 2D projection of 3D candidate lattice: 5x5x5 = 125 points
        # Coordinates: x, y, z in {-2, -1, 0, 1, 2}
        # Projection: X = 0.65*x + 0.35*z, Y = 0.65*y + 0.2*z - 0.3
        points_all = list(itertools.product(range(-2, 3), repeat=3))
        dots_all = VGroup()

        for x, y, z in points_all:
            px = 0.75 * x + 0.35 * z - 2.8
            py = 0.70 * y + 0.20 * z - 0.4
            # Color by depth z
            dot_col = COLOR_BLUE if z >= 0 else COLOR_TEAL
            dot = Dot(point=[px, py, 0.0], radius=0.065, color=dot_col)
            dots_all.add(dot)

        universe_hud = (
            RoundedRectangle(
                corner_radius=0.12,
                width=5.4,
                height=2.4,
                color=COLOR_BLUE,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            .to_edge(RIGHT, buff=0.8)
            .shift(UP * 0.5)
        )

        u_t1 = Text("Candidate Universe", font_size=18, color=COLOR_BLUE, weight="BOLD").move_to(
            universe_hud.get_top() + DOWN * 0.35
        )
        u_t2 = Text("Alphabet: {-2, -1, 0, 1, 2}³", font_size=14, color=COLOR_WHITE).next_to(
            u_t1, DOWN, buff=0.15
        )
        u_t3 = Text("|U| = 125 States", font_size=26, color=COLOR_YELLOW, weight="BOLD").next_to(
            u_t2, DOWN, buff=0.2
        )
        u_card = VGroup(universe_hud, u_t1, u_t2, u_t3)

        self.play(FadeIn(dots_all), FadeIn(u_card), run_time=1.2)
        self.wait(1.0)

        # ---------------------------------------------------------------------
        # Act II: Anti-Morphisms: PIN & SHAPE Filters (0:25 - 0:50)
        # ---------------------------------------------------------------------
        filter_banner = RoundedRectangle(
            corner_radius=0.1,
            width=5.4,
            height=2.2,
            color=COLOR_TEAL,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=2,
        ).next_to(universe_hud, DOWN, buff=0.3)

        f_t1 = Text(
            "Anti-Morphism Operators", font_size=16, color=COLOR_TEAL, weight="BOLD"
        ).move_to(filter_banner.get_top() + DOWN * 0.3)
        f_t2 = Text("1. PIN: Codepoint validation", font_size=13, color=COLOR_WHITE).next_to(
            f_t1, DOWN, buff=0.15
        )
        f_t3 = Text("2. SHAPE: Arity checking", font_size=13, color=COLOR_WHITE).next_to(
            f_t2, DOWN, buff=0.12
        )
        f_t4 = Text(
            "3. LAND_ON_ZERO: Φ₁ = 0", font_size=13, color=COLOR_YELLOW, weight="BOLD"
        ).next_to(f_t3, DOWN, buff=0.12)

        filter_card = VGroup(filter_banner, f_t1, f_t2, f_t3, f_t4)
        self.play(FadeIn(filter_card), run_time=0.8)

        # ---------------------------------------------------------------------
        # Act III: Collapse to RESIDUAL (19) and LANDED (1) (0:50 - 1:25)
        # ---------------------------------------------------------------------
        # The 19 cycle-consistent points satisfy x + y + z = 0 in the 3-cycle
        residual_indices = [i for i, (x, y, z) in enumerate(points_all) if x + y + z == 0]
        assert len(residual_indices) == 19

        non_residual_dots = VGroup(
            *[dots_all[i] for i in range(len(points_all)) if i not in residual_indices]
        )
        residual_dots = VGroup(*[dots_all[i] for i in residual_indices])

        # Step 1: Slice non-consistent points
        u_t3_res = Text(
            "|A₁| = 19 (RESIDUAL)", font_size=24, color=COLOR_YELLOW, weight="BOLD"
        ).move_to(u_t3)
        self.play(
            non_residual_dots.animate.set_opacity(0.06),
            residual_dots.animate.set_color(COLOR_YELLOW),
            ReplacementTransform(u_t3, u_t3_res),
            run_time=1.2,
        )
        self.wait(1.0)

        # Step 2: Adaptive demand prefix (1, -1) -> exactly (1, -1, 0) survives
        landed_index = [i for i in residual_indices if points_all[i][:2] == (1, -1)][0]
        assert points_all[landed_index] == (1, -1, 0)

        other_residual_dots = VGroup(*[dots_all[i] for i in residual_indices if i != landed_index])
        landed_dot = dots_all[landed_index]

        u_t3_land = Text(
            "|A₂| = 1 (LANDED)", font_size=24, color=COLOR_GREEN, weight="BOLD"
        ).move_to(u_t3_res)
        demand_banner = Text(
            "Host Issues DEMAND: prefix == (1, -1)",
            font_size=16,
            color=COLOR_YELLOW,
            weight="BOLD",
        ).to_edge(DOWN, buff=0.8)

        witness_box = Text(
            "Witness Found: (1, -1, 0)",
            font_size=20,
            color=COLOR_GREEN,
            weight="BOLD",
        ).next_to(demand_banner, UP, buff=0.25)

        self.play(
            FadeIn(demand_banner),
            other_residual_dots.animate.set_opacity(0.06),
            landed_dot.animate.scale(2.5).set_color(COLOR_GREEN),
            ReplacementTransform(u_t3_res, u_t3_land),
            FadeIn(witness_box),
            run_time=1.2,
        )
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act IV: Contrast Path: Contradictory Demand -> REFUSED_EMPTY (1:25 - 1:45)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(demand_banner),
            FadeOut(witness_box),
            FadeOut(dots_all),
            FadeOut(u_card),
            FadeOut(filter_card),
            run_time=0.8,
        )

        refusal_box = RoundedRectangle(
            corner_radius=0.15,
            width=8.5,
            height=3.2,
            color=COLOR_RED,
            fill_color=COLOR_CARD,
            fill_opacity=0.95,
            stroke_width=2.5,
        ).move_to(DOWN * 0.2)

        ref_t1 = Text(
            "CONTRADICTORY DEMAND INJECTION", font_size=20, color=COLOR_RED, weight="BOLD"
        ).move_to(refusal_box.get_top() + DOWN * 0.4)
        ref_t2 = Text(
            "Demand: sum(claims) == 99  (No Admissible States)", font_size=15, color=COLOR_WHITE
        ).next_to(ref_t1, DOWN, buff=0.2)
        ref_t3 = Text(
            "Manifold Fixpoint: A_∞ = ∅ (Empty Set)", font_size=18, color=COLOR_YELLOW
        ).next_to(ref_t2, DOWN, buff=0.2)
        ref_t4 = Text(
            "STATUS: REFUSED_EMPTY (Typed Refusal)", font_size=22, color=COLOR_RED, weight="BOLD"
        ).next_to(ref_t3, DOWN, buff=0.25)

        ref_card = VGroup(refusal_box, ref_t1, ref_t2, ref_t3, ref_t4)
        self.play(FadeIn(ref_card), run_time=1.0)

        moral = Text(
            "An honest, typed refusal is more informative than a hallucinated point.",
            font_size=15,
            color=COLOR_WHITE,
        ).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(moral), run_time=0.8)
        self.wait(2.0)


if __name__ == "__main__":
    print("Run with: manim -qm -s scenes/scene4_token_manifold_collapse.py TokenManifoldCollapse")
