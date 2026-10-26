"""Scene 5: Local Green / Global Red Boundary Conflicts.

Visualizes:
  1. Three overlapping local domains U_1, U_2, U_3 in a triad cover.
  2. Local evaluations: Patch 1 = GREEN, Patch 2 = GREEN, Patch 3 = GREEN.
  3. Pairwise consistency: Overlaps U_1 n U_2, U_2 n U_3, U_3 n U_1 match cleanly.
  4. Macroscopic loop frustration: Holonomy accumulation around the cycle.
  5. Global collapse: Boundary flashes intense RED (Global Obstruction).
  6. The Asymmetric Verdict Law:
     RED is sound (witnesses obstruction) | GREEN is unsound (local only).
  7. Formal grounding from PrimitiveDifference.lean: localGreenGlobalRed_pair_obstruction_of_witness.

Render sample frame:
    manim -qm -s scenes/scene5_lggr_boundary_conflicts.py LggrBoundaryConflicts

AuthorityEffect: None.
Claim Hygiene: Diagnostic sheaf analogy; demonstrates the Asymmetric Verdict Law.
"""

from __future__ import annotations

import math

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
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


class LggrBoundaryConflicts(Scene):
    """Main animation scene for Scene 5: Local Green / Global Red Boundary Conflicts."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------------------
        # Act I: Local Evaluators & Triad Patches (0:00 - 0:30)
        # ---------------------------------------------------------------------
        title = Text("Local Green / Global Red", font_size=38, color=COLOR_WHITE, weight="BOLD")
        subtitle = Text(
            "Boundary Conflicts & Asymmetric Verification", font_size=22, color=COLOR_BLUE
        )
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.15).to_edge(UP, buff=0.4)
        self.play(FadeIn(title_group), run_time=1.0)
        self.wait(0.5)

        # Three overlapping circular domains U_1, U_2, U_3 in equilateral layout
        radius_cover = 1.35
        dist_center = 1.15

        c1 = dist_center * UP * 0.9 + LEFT * 2.8 + DOWN * 0.2
        c2 = (
            dist_center
            * (math.cos(math.radians(210)) * RIGHT + math.sin(math.radians(210)) * UP)
            * 0.9
            + LEFT * 2.8
            + DOWN * 0.2
        )
        c3 = (
            dist_center
            * (math.cos(math.radians(330)) * RIGHT + math.sin(math.radians(330)) * UP)
            * 0.9
            + LEFT * 2.8
            + DOWN * 0.2
        )

        patch1 = Circle(
            radius=radius_cover,
            color=COLOR_BLUE,
            fill_color=COLOR_BLUE,
            fill_opacity=0.25,
            stroke_width=2.5,
        ).move_to(c1)
        patch2 = Circle(
            radius=radius_cover,
            color=COLOR_TEAL,
            fill_color=COLOR_TEAL,
            fill_opacity=0.25,
            stroke_width=2.5,
        ).move_to(c2)
        patch3 = Circle(
            radius=radius_cover,
            color=COLOR_PURPLE,
            fill_color=COLOR_PURPLE,
            fill_opacity=0.25,
            stroke_width=2.5,
        ).move_to(c3)

        l1 = Text("U₁", font_size=20, color=COLOR_WHITE, weight="BOLD").move_to(c1 + UP * 0.4)
        l2 = Text("U₂", font_size=20, color=COLOR_WHITE, weight="BOLD").move_to(
            c2 + DOWN * 0.4 + LEFT * 0.3
        )
        l3 = Text("U₃", font_size=20, color=COLOR_WHITE, weight="BOLD").move_to(
            c3 + DOWN * 0.4 + RIGHT * 0.3
        )

        patches_vg = VGroup(patch1, patch2, patch3, l1, l2, l3)
        self.play(FadeIn(patches_vg), run_time=1.0)

        # Local Evaluator Badges
        b1 = Text("✓ GREEN (Φ₁=0)", font_size=13, color=COLOR_GREEN, weight="BOLD").next_to(
            l1, DOWN, buff=0.15
        )
        b2 = Text("✓ GREEN (Φ₁=0)", font_size=13, color=COLOR_GREEN, weight="BOLD").next_to(
            l2, UP, buff=0.15
        )
        b3 = Text("✓ GREEN (Φ₁=0)", font_size=13, color=COLOR_GREEN, weight="BOLD").next_to(
            l3, UP, buff=0.15
        )

        eval_card = (
            RoundedRectangle(
                corner_radius=0.12,
                width=5.8,
                height=2.8,
                color=COLOR_GREEN,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            .to_edge(RIGHT, buff=0.8)
            .shift(DOWN * 0.2)
        )

        ec_t1 = Text("LOCAL EVALUATIONS", font_size=18, color=COLOR_GREEN, weight="BOLD").move_to(
            eval_card.get_top() + DOWN * 0.35
        )
        ec_t2 = Text("• Patch U₁: Verified Consistent", font_size=14, color=COLOR_WHITE).next_to(
            ec_t1, DOWN, buff=0.2
        )
        ec_t3 = Text("• Patch U₂: Verified Consistent", font_size=14, color=COLOR_WHITE).next_to(
            ec_t2, DOWN, buff=0.15
        )
        ec_t4 = Text("• Patch U₃: Verified Consistent", font_size=14, color=COLOR_WHITE).next_to(
            ec_t3, DOWN, buff=0.15
        )
        ec_t5 = Text(
            "Local Status: 100% GREEN", font_size=16, color=COLOR_GREEN, weight="BOLD"
        ).next_to(ec_t4, DOWN, buff=0.2)

        eval_info = VGroup(eval_card, ec_t1, ec_t2, ec_t3, ec_t4, ec_t5)

        self.play(FadeIn(b1), FadeIn(b2), FadeIn(b3), FadeIn(eval_info), run_time=1.0)
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act II: Pairwise Overlaps vs Global Holonomy Mismatch (0:30 - 1:05)
        # ---------------------------------------------------------------------
        # Show pairwise overlap check
        overlap_note = Text(
            "Pairwise Overlaps (U₁∩U₂, U₂∩U₃, U₃∩U₁) Match.",
            font_size=14,
            color=COLOR_YELLOW,
        ).to_edge(DOWN, buff=1.2)
        self.play(FadeIn(overlap_note), run_time=0.6)
        self.wait(1.0)

        # Global gluing attempt: a red loop traces the central hole
        (c1 + c2 + c3) / 3
        tracker = Dot(color=COLOR_YELLOW, radius=0.14).move_to(c1)
        self.play(FadeIn(tracker), run_time=0.3)

        # Trace loop c1 -> c2 -> c3 -> c1
        self.play(tracker.animate.move_to(c2), run_time=0.5)
        self.play(tracker.animate.move_to(c3), run_time=0.5)
        self.play(tracker.animate.move_to(c1), run_time=0.5)

        # Holonomy accumulates -> Flash RED!
        eval_card_red = RoundedRectangle(
            corner_radius=0.12,
            width=5.8,
            height=2.8,
            color=COLOR_RED,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=2.5,
        ).move_to(eval_card)

        er_t1 = Text("GLOBAL EVALUATION", font_size=18, color=COLOR_RED, weight="BOLD").move_to(
            eval_card_red.get_top() + DOWN * 0.35
        )
        er_t2 = Text("• Loop Holonomy Mismatch != 0", font_size=14, color=COLOR_RED).next_to(
            er_t1, DOWN, buff=0.2
        )
        er_t3 = Text("• Non-zero Obstruction Class", font_size=14, color=COLOR_WHITE).next_to(
            er_t2, DOWN, buff=0.15
        )
        er_t4 = Text("• Sections Fail to Glue Globally", font_size=14, color=COLOR_WHITE).next_to(
            er_t3, DOWN, buff=0.15
        )
        er_t5 = Text("GLOBAL STATUS: RED", font_size=18, color=COLOR_RED, weight="BOLD").next_to(
            er_t4, DOWN, buff=0.2
        )

        eval_info_red = VGroup(eval_card_red, er_t1, er_t2, er_t3, er_t4, er_t5)

        global_banner = Text(
            "Macroscopic Frustration: Local Green, Global Red!",
            font_size=18,
            color=COLOR_RED,
            weight="BOLD",
        ).move_to(overlap_note)

        self.play(
            ReplacementTransform(eval_info, eval_info_red),
            ReplacementTransform(overlap_note, global_banner),
            patch1.animate.set_stroke(color=COLOR_RED, width=3.5),
            patch2.animate.set_stroke(color=COLOR_RED, width=3.5),
            patch3.animate.set_stroke(color=COLOR_RED, width=3.5),
            run_time=1.0,
        )
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act III: The Asymmetric Verdict Law (1:05 - 1:45)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(tracker),
            FadeOut(patches_vg),
            FadeOut(b1),
            FadeOut(b2),
            FadeOut(b3),
            FadeOut(eval_info_red),
            FadeOut(global_banner),
            run_time=0.8,
        )

        asym_box = RoundedRectangle(
            corner_radius=0.15,
            width=9.8,
            height=3.8,
            color=COLOR_YELLOW,
            fill_color=COLOR_CARD,
            fill_opacity=0.95,
            stroke_width=2,
        ).move_to(DOWN * 0.2)

        asym_title = Text(
            "THE ASYMMETRIC VERDICT LAW", font_size=22, color=COLOR_YELLOW, weight="BOLD"
        ).move_to(asym_box.get_top() + DOWN * 0.4)

        red_law = Text(
            "RED is Sound:  A single obstruction witnesses that no global section exists.",
            font_size=14,
            color=COLOR_RED,
            weight="BOLD",
        ).next_to(asym_title, DOWN, buff=0.35)

        green_law = Text(
            "GREEN is Unsound:  Local consensus does NOT guarantee global consistency.",
            font_size=14,
            color=COLOR_GREEN,
            weight="BOLD",
        ).next_to(red_law, DOWN, buff=0.25)

        formal_lemma = Text(
            "Theorem: localGreenGlobalRed_pair_obstruction_of_witness\n(OmegaCore / PrimitiveDifference.lean)",
            font_size=13,
            color=COLOR_TEAL,
        ).next_to(green_law, DOWN, buff=0.25)

        asym_vg = VGroup(asym_box, asym_title, red_law, green_law, formal_lemma)
        self.play(FadeIn(asym_vg), run_time=1.0)

        moral = Text(
            "Principle: No local agent's green badge can authorize global completion.",
            font_size=15,
            color=COLOR_WHITE,
            weight="BOLD",
        ).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(moral), run_time=0.8)
        self.wait(2.0)


if __name__ == "__main__":
    print("Run with: manim -qm -s scenes/scene5_lggr_boundary_conflicts.py LggrBoundaryConflicts")
