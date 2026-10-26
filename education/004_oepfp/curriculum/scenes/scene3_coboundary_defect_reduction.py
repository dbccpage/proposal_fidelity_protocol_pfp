"""Scene 3: Coboundary Operators & Defect Reduction.

Visualizes:
  1. Low-degree cochain spaces C^0 (vertices), C^1 (edges), C^2 (faces).
  2. Coboundary operator d^0: C^0 -> C^1, (d^0 f)(u->v) = f(v) - f(u).
  3. Coboundary operator d^1: C^1 -> C^2, (d^1 c)(F) = sum around face boundary.
  4. Fundamental nilpotency identity: d^1 o d^0 = 0 (boundary of boundary is empty).
  5. Dual defect metrics:
     - Primary obstruction Phi_1 = min_f ||c - d^0 f||_{1, w}
     - Face curvature defect Gamma_2 = ||d^1 c||_1
  6. Synchronized monotonic defect descent (3 -> 1 -> 0).
  7. Fail-closed defense gate: DefectIncrease -> REFUSED.

Render sample frame:
    manim -qm -s scenes/scene3_coboundary_defect_reduction.py CoboundaryDefectReduction

AuthorityEffect: None.
Claim Hygiene: Toy cochain complex; illustrates coboundary operators on a 2-cell.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Create,
    FadeIn,
    FadeOut,
    Polygon,
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


class CoboundaryDefectReduction(Scene):
    """Main animation scene for Scene 3: Coboundary Operators & Defect Reduction."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------------------
        # Act I: Vertex Potentials & Coboundary d^0 (0:00 - 0:30)
        # ---------------------------------------------------------------------
        title = Text(
            "Coboundary Operators & Defect Reduction",
            font_size=36,
            color=COLOR_WHITE,
            weight="BOLD",
        )
        subtitle = Text("Low-Degree Cochain Dynamics (C⁰, C¹, C²)", font_size=22, color=COLOR_BLUE)
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.15).to_edge(UP, buff=0.4)
        self.play(FadeIn(title_group), run_time=1.0)
        self.wait(0.5)

        # Show two vertices with potential values
        p_u = LEFT * 3.0 + UP * 0.5
        p_v = RIGHT * 1.5 + UP * 0.5

        node_u = Circle(
            radius=0.45, color=COLOR_BLUE, fill_color=COLOR_CARD, fill_opacity=0.9, stroke_width=3
        ).move_to(p_u)
        lbl_u = Text("u", font_size=22, color=COLOR_WHITE, weight="BOLD").move_to(p_u)
        pot_u = Text("f(u) = 2", font_size=16, color=COLOR_YELLOW).next_to(node_u, UP, buff=0.2)
        vg_u = VGroup(node_u, lbl_u, pot_u)

        node_v = Circle(
            radius=0.45, color=COLOR_BLUE, fill_color=COLOR_CARD, fill_opacity=0.9, stroke_width=3
        ).move_to(p_v)
        lbl_v = Text("v", font_size=22, color=COLOR_WHITE, weight="BOLD").move_to(p_v)
        pot_v = Text("f(v) = 5", font_size=16, color=COLOR_YELLOW).next_to(node_v, UP, buff=0.2)
        vg_v = VGroup(node_v, lbl_v, pot_v)

        self.play(FadeIn(vg_u), FadeIn(vg_v), run_time=0.8)

        # Directed edge u -> v
        edge_uv = Arrow(p_u, p_v, buff=0.52, color=COLOR_BLUE, stroke_width=4)
        cob_formula = Text(
            "(δ⁰ f)(u→v) = f(v) - f(u) = 5 - 2 = 3",
            font_size=18,
            color=COLOR_GREEN,
            weight="BOLD",
        ).next_to(edge_uv, DOWN, buff=0.25)

        self.play(Create(edge_uv), FadeIn(cob_formula), run_time=1.0)

        d0_card = RoundedRectangle(
            corner_radius=0.1,
            width=8.5,
            height=0.8,
            color=COLOR_BLUE,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=1.5,
        ).to_edge(DOWN, buff=0.8)
        d0_note = Text(
            "Coboundary δ⁰ : C⁰ → C¹ maps 0-cochains (potentials) to 1-cochains (edge claims).",
            font_size=13,
            color=COLOR_WHITE,
        ).move_to(d0_card)
        self.play(FadeIn(d0_card), FadeIn(d0_note), run_time=0.6)
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act II: Face Curvature d^1 & Nilpotency d^1 o d^0 = 0 (0:30 - 1:00)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(vg_u),
            FadeOut(vg_v),
            FadeOut(edge_uv),
            FadeOut(cob_formula),
            FadeOut(d0_card),
            FadeOut(d0_note),
            run_time=0.8,
        )

        face_title = Text(
            "Face Curvature δ¹ & Nilpotency δ¹ ∘ δ⁰ = 0", font_size=22, color=COLOR_YELLOW
        ).next_to(title_group, DOWN, buff=0.3)
        self.play(FadeIn(face_title), run_time=0.6)

        # Triangle 2-cell
        p_a = LEFT * 3.5 + DOWN * 1.0
        p_b = LEFT * 0.5 + DOWN * 1.0
        p_c = LEFT * 2.0 + UP * 1.3

        tri_face = Polygon(
            p_a,
            p_b,
            p_c,
            color=COLOR_PURPLE,
            fill_color=COLOR_PURPLE,
            fill_opacity=0.25,
            stroke_width=2,
        )
        face_lbl = Text("Face F ∈ C²", font_size=14, color=COLOR_PURPLE, weight="BOLD").move_to(
            (p_a + p_b + p_c) / 3
        )

        e1 = Arrow(p_a, p_b, buff=0.1, color=COLOR_BLUE, stroke_width=3)
        e2 = Arrow(p_b, p_c, buff=0.1, color=COLOR_BLUE, stroke_width=3)
        e3 = Arrow(p_c, p_a, buff=0.1, color=COLOR_BLUE, stroke_width=3)

        l1 = Text("e₁", font_size=13, color=COLOR_WHITE).next_to(e1, DOWN, buff=0.1)
        l2 = Text("e₂", font_size=13, color=COLOR_WHITE).next_to(e2, RIGHT, buff=0.1)
        l3 = Text("e₃", font_size=13, color=COLOR_WHITE).next_to(e3, LEFT, buff=0.1)

        tri_group = VGroup(tri_face, face_lbl, e1, e2, e3, l1, l2, l3)
        self.play(FadeIn(tri_group), run_time=1.0)

        # Formula card on right
        nilpotency_box = (
            RoundedRectangle(
                corner_radius=0.12,
                width=5.8,
                height=3.2,
                color=COLOR_TEAL,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            .to_edge(RIGHT, buff=0.8)
            .shift(DOWN * 0.2)
        )

        n_t1 = Text("Boundary Operators:", font_size=16, color=COLOR_TEAL, weight="BOLD").move_to(
            nilpotency_box.get_top() + DOWN * 0.35
        )
        n_t2 = Text("(δ¹ c)(F) = c(e₁) + c(e₂) + c(e₃)", font_size=15, color=COLOR_WHITE).next_to(
            n_t1, DOWN, buff=0.2
        )
        n_t3 = Text("Composition on Exact Potentials:", font_size=14, color=COLOR_MUTED).next_to(
            n_t2, DOWN, buff=0.2
        )
        n_t4 = Text("δ¹ ∘ δ⁰ ≡ 0", font_size=24, color=COLOR_GREEN, weight="BOLD").next_to(
            n_t3, DOWN, buff=0.15
        )
        n_t5 = Text(
            "The boundary of a boundary is empty.", font_size=13, color=COLOR_WHITE
        ).next_to(n_t4, DOWN, buff=0.15)

        nil_card = VGroup(nilpotency_box, n_t1, n_t2, n_t3, n_t4, n_t5)
        self.play(FadeIn(nil_card), run_time=0.8)
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act III: Dual Defect Reduction (Phi_1 & Gamma_2 Descent) (1:00 - 1:30)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(face_title),
            FadeOut(tri_group),
            FadeOut(nil_card),
            run_time=0.8,
        )

        hud_title = Text("Dual Defect Reduction Gauges", font_size=22, color=COLOR_YELLOW).next_to(
            title_group, DOWN, buff=0.3
        )
        self.play(FadeIn(hud_title), run_time=0.6)

        # Left gauge: Phi_1 (Scalar Primary Obstruction)
        g1_box = RoundedRectangle(
            corner_radius=0.12,
            width=5.0,
            height=2.4,
            color=COLOR_BLUE,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=2,
        ).move_to(LEFT * 3.0 + DOWN * 0.4)

        g1_title = Text(
            "Primary Obstruction: Φ₁", font_size=16, color=COLOR_BLUE, weight="BOLD"
        ).move_to(g1_box.get_top() + DOWN * 0.35)
        g1_def = Text("Φ₁(c) = min ||c - δ⁰f||₁,w", font_size=13, color=COLOR_MUTED).next_to(
            g1_title, DOWN, buff=0.15
        )
        g1_val = Text("Φ₁ = 3.0", font_size=28, color=COLOR_RED, weight="BOLD").next_to(
            g1_def, DOWN, buff=0.2
        )
        gauge1 = VGroup(g1_box, g1_title, g1_def, g1_val)

        # Right gauge: Gamma_2 (Curvature Defect)
        g2_box = RoundedRectangle(
            corner_radius=0.12,
            width=5.0,
            height=2.4,
            color=COLOR_PURPLE,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=2,
        ).move_to(RIGHT * 3.0 + DOWN * 0.4)

        g2_title = Text(
            "Curvature Defect: Γ₂", font_size=16, color=COLOR_PURPLE, weight="BOLD"
        ).move_to(g2_box.get_top() + DOWN * 0.35)
        g2_def = Text("Γ₂(c) = ||δ¹ c||₁", font_size=13, color=COLOR_MUTED).next_to(
            g2_title, DOWN, buff=0.15
        )
        g2_val = Text("Γ₂ = 3.0", font_size=28, color=COLOR_RED, weight="BOLD").next_to(
            g2_def, DOWN, buff=0.2
        )
        gauge2 = VGroup(g2_box, g2_title, g2_def, g2_val)

        self.play(FadeIn(gauge1), FadeIn(gauge2), run_time=1.0)
        self.wait(0.5)

        # Animate Monotone Descent Step 1: 3.0 -> 1.0
        step1_lbl = Text(
            "Descent Step 1: Repairing heaviest edge...", font_size=15, color=COLOR_YELLOW
        ).to_edge(DOWN, buff=1.2)
        g1_v2 = Text("Φ₁ = 1.0", font_size=28, color=COLOR_YELLOW, weight="BOLD").move_to(g1_val)
        g2_v2 = Text("Γ₂ = 1.0", font_size=28, color=COLOR_YELLOW, weight="BOLD").move_to(g2_val)

        self.play(
            FadeIn(step1_lbl),
            ReplacementTransform(g1_val, g1_v2),
            ReplacementTransform(g2_val, g2_v2),
            run_time=0.8,
        )
        self.wait(0.6)

        # Step 2: 1.0 -> 0.0 (Zero Defect)
        step2_lbl = Text(
            "Descent Step 2: Reaching coboundary fixpoint...", font_size=15, color=COLOR_GREEN
        ).move_to(step1_lbl)
        g1_v3 = Text("Φ₁ = 0.0", font_size=28, color=COLOR_GREEN, weight="BOLD").move_to(g1_val)
        g2_v3 = Text("Γ₂ = 0.0", font_size=28, color=COLOR_GREEN, weight="BOLD").move_to(g2_val)

        self.play(
            ReplacementTransform(step1_lbl, step2_lbl),
            ReplacementTransform(g1_v2, g1_v3),
            ReplacementTransform(g2_v2, g2_v3),
            g1_box.animate.set_stroke(color=COLOR_GREEN),
            g2_box.animate.set_stroke(color=COLOR_GREEN),
            run_time=0.8,
        )
        self.wait(1.0)

        # ---------------------------------------------------------------------
        # Act IV: Fail-Closed Defense Gate (1:30 - 1:50)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(step2_lbl),
            run_time=0.4,
        )

        adversarial_box = RoundedRectangle(
            corner_radius=0.15,
            width=9.5,
            height=1.2,
            color=COLOR_RED,
            fill_color=COLOR_CARD,
            fill_opacity=0.95,
            stroke_width=3,
        ).to_edge(DOWN, buff=0.6)

        adv_title = Text(
            "Adversarial Proposal: Increases Defect (0.0 → 2.0)",
            font_size=15,
            color=COLOR_RED,
            weight="BOLD",
        ).move_to(adversarial_box.get_center() + UP * 0.2)
        adv_action = Text(
            "GATE ACTION: DefectIncrease → REFUSED (Fail-Closed)",
            font_size=16,
            color=COLOR_RED,
            weight="BOLD",
        ).move_to(adversarial_box.get_center() + DOWN * 0.2)

        adv_gate = VGroup(adversarial_box, adv_title, adv_action)
        self.play(FadeIn(adv_gate, shift=UP * 0.2), run_time=0.8)
        self.wait(2.0)


if __name__ == "__main__":
    print(
        "Run with: manim -qm -s scenes/scene3_coboundary_defect_reduction.py CoboundaryDefectReduction"
    )
