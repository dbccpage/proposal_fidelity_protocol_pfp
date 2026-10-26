"""Scene 2: S(N) Tower Construction from Primitive Differences.

Visualizes:
  1. Primitive difference from Genesis axioms: irreflexive witnessed distinction delta(x, y) != 0.
  2. Minimal carrier Bool (False, True) and automorphism breaking.
  3. Diagonal excision: (V x V) \\ Delta removes self-identity.
  4. Arity filtration and the S(N) Tower (Stages 0 through 5):
     - S_0: Empty carrier / ground (arity 0)
     - S_1: Singletons / points (arity 1)
     - S_2: Pairs / relations (arity 2)
     - S_3: Triangles / 2-cells (arity 3)
     - S_4: Tetrahedra / 3-cells (arity 4)
     - S_5: Higher simplicial complexes S_n
  5. Bounded hierarchy: no unpriced rewrites across the tower.

Render sample frame:
    manim -qm -s scenes/scene2_sn_tower_construction.py SnTowerConstruction

AuthorityEffect: None.
Claim Hygiene: Toy simplicial representation; illustrates formal relation from PrimitiveDifference.lean.
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
    RoundedRectangle,
    Scene,
    Square,
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


class SnTowerConstruction(Scene):
    """Main animation scene for Scene 2: S(N) Tower Construction."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------------------
        # Act I: The Primitive Difference (0:00 - 0:25)
        # ---------------------------------------------------------------------
        title = Text("S(N) Tower Construction", font_size=38, color=COLOR_WHITE, weight="BOLD")
        subtitle = Text(
            "From Primitive Differences to Simplicial Filtration", font_size=22, color=COLOR_BLUE
        )
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.15).to_edge(UP, buff=0.4)
        self.play(FadeIn(title_group), run_time=1.0)
        self.wait(0.5)

        # Two distinct nodes x and y
        p_x = LEFT * 2.5 + DOWN * 0.2
        p_y = RIGHT * 2.5 + DOWN * 0.2

        node_x = Circle(
            radius=0.45, color=COLOR_BLUE, fill_color=COLOR_CARD, fill_opacity=0.9, stroke_width=3
        ).move_to(p_x)
        lbl_x = Text("x", font_size=26, color=COLOR_WHITE, weight="BOLD").move_to(p_x)
        vg_x = VGroup(node_x, lbl_x)

        node_y = Circle(
            radius=0.45, color=COLOR_TEAL, fill_color=COLOR_CARD, fill_opacity=0.9, stroke_width=3
        ).move_to(p_y)
        lbl_y = Text("y", font_size=26, color=COLOR_WHITE, weight="BOLD").move_to(p_y)
        vg_y = VGroup(node_y, lbl_y)

        self.play(FadeIn(vg_x), FadeIn(vg_y), run_time=0.8)

        # Directed distinction arrow
        dist_arrow = Arrow(p_x, p_y, buff=0.55, color=COLOR_YELLOW, stroke_width=4)
        dist_label = Text("δ(x, y) ≠ 0", font_size=20, color=COLOR_YELLOW).next_to(
            dist_arrow, UP, buff=0.2
        )
        dist_sub = Text("Irreflexive Witness: x ≁ x", font_size=15, color=COLOR_MUTED).next_to(
            dist_arrow, DOWN, buff=0.2
        )

        self.play(Create(dist_arrow), FadeIn(dist_label), FadeIn(dist_sub), run_time=1.0)

        # Reference to Lean formalization
        lean_badge = RoundedRectangle(
            corner_radius=0.1,
            width=5.8,
            height=0.6,
            color=COLOR_BLUE,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=1.5,
        ).to_edge(DOWN, buff=0.5)
        lean_text = Text(
            "Formalized: lean4/PrimitiveDifference.lean", font_size=14, color=COLOR_TEAL
        ).move_to(lean_badge)
        self.play(FadeIn(lean_badge), FadeIn(lean_text), run_time=0.6)
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act II: Minimal Carrier Bool & Diagonal Excision (0:25 - 0:50)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(vg_x),
            FadeOut(vg_y),
            FadeOut(dist_arrow),
            FadeOut(dist_label),
            FadeOut(dist_sub),
            FadeOut(lean_badge),
            FadeOut(lean_text),
            run_time=0.8,
        )

        bool_header = Text(
            "Minimal Carrier: Bool = {false, true}", font_size=22, color=COLOR_YELLOW
        ).next_to(title_group, DOWN, buff=0.3)
        self.play(FadeIn(bool_header), run_time=0.6)

        # Show product space V x V as 2x2 grid
        grid_vg = VGroup()
        grid_size = 1.4
        grid_origin = LEFT * 3.5 + DOWN * 0.5

        cells_data = [
            (0, 0, "(f, f)", True),
            (0, 1, "(f, t)", False),
            (1, 0, "(t, f)", False),
            (1, 1, "(t, t)", True),
        ]
        diag_cells = VGroup()
        rel_cells = VGroup()

        for r, c, txt, is_diag in cells_data:
            pos = grid_origin + RIGHT * (c * grid_size) + DOWN * (r * grid_size)
            sq = Square(
                side_length=grid_size * 0.92,
                color=COLOR_RED if is_diag else COLOR_BLUE,
                fill_color=COLOR_CARD,
                fill_opacity=0.85,
                stroke_width=2,
            ).move_to(pos)
            lab = Text(txt, font_size=16, color=COLOR_RED if is_diag else COLOR_WHITE).move_to(pos)
            cell = VGroup(sq, lab)
            if is_diag:
                diag_cells.add(cell)
            else:
                rel_cells.add(cell)
            grid_vg.add(cell)

        grid_label = Text("Product Space: V × V", font_size=16, color=COLOR_WHITE).next_to(
            grid_vg, UP, buff=0.25
        )
        self.play(FadeIn(grid_label), FadeIn(grid_vg), run_time=1.0)

        # Excision explanation card
        excision_card = (
            RoundedRectangle(
                corner_radius=0.12,
                width=5.8,
                height=2.8,
                color=COLOR_YELLOW,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            .to_edge(RIGHT, buff=0.8)
            .shift(DOWN * 0.5)
        )

        card_title = Text(
            "Diagonal Excision: (V × V) \\ Δ", font_size=18, color=COLOR_YELLOW, weight="BOLD"
        ).move_to(excision_card.get_top() + DOWN * 0.35)
        card_l1 = Text(
            "Δ = {(v, v) : v ∈ V}  (Self-Identity)", font_size=14, color=COLOR_RED
        ).next_to(card_title, DOWN, buff=0.2)
        card_l2 = Text(
            "Excising Δ eliminates trivial relations.", font_size=14, color=COLOR_WHITE
        ).next_to(card_l1, DOWN, buff=0.15)
        card_l3 = Text(
            "Leaves witnessed differences only:", font_size=14, color=COLOR_WHITE
        ).next_to(card_l2, DOWN, buff=0.15)
        card_l4 = Text(
            "{(false, true), (true, false)}", font_size=16, color=COLOR_GREEN, weight="BOLD"
        ).next_to(card_l3, DOWN, buff=0.15)

        excision_info = VGroup(excision_card, card_title, card_l1, card_l2, card_l3, card_l4)
        self.play(FadeIn(excision_info), run_time=0.8)

        # Animate diagonal cells flashing red and dissolving
        self.play(
            diag_cells.animate.set_opacity(0.15),
            rel_cells.animate.set_stroke(color=COLOR_GREEN, width=3),
            run_time=1.0,
        )
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act III: The Rising S(N) Tower (Stages 0 - 5) (0:50 - 1:25)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(bool_header),
            FadeOut(grid_label),
            FadeOut(grid_vg),
            FadeOut(excision_info),
            run_time=0.8,
        )

        tower_title = Text(
            "Arity Filtration: Stages 0 through 5", font_size=22, color=COLOR_YELLOW
        ).next_to(title_group, DOWN, buff=0.3)
        self.play(FadeIn(tower_title), run_time=0.6)

        tower_levels = [
            (
                "Stage 5",
                "S₅: Higher Simplicial Complexes",
                "Degree-k cocycle constraints",
                COLOR_PURPLE,
            ),
            ("Stage 4", "S₄: 3-Cells / Tetrahedra", "Volume boundary closure d²=0", COLOR_BLUE),
            ("Stage 3", "S₃: 2-Cells / Triangles", "Face curvature & holonomy d¹", COLOR_TEAL),
            ("Stage 2", "S₂: 1-Cells / Directed Edges", "Pairwise relation claims d⁰", COLOR_GREEN),
            ("Stage 1", "S₁: 0-Cells / Singletons", "Vertex carrier elements", COLOR_YELLOW),
            ("Stage 0", "S₀: Empty Carrier ∅", "Primitive ground distinction", COLOR_MUTED),
        ]

        tower_vg = VGroup()
        bar_width = 8.5
        bar_height = 0.55

        for stg, name, desc, col in tower_levels:
            bar = RoundedRectangle(
                corner_radius=0.08,
                width=bar_width,
                height=bar_height,
                color=col,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            s_tag = Text(stg, font_size=13, color=col, weight="BOLD").move_to(
                bar.get_left() + RIGHT * 0.7
            )
            t_name = Text(name, font_size=13, color=COLOR_WHITE, weight="BOLD").next_to(
                s_tag, RIGHT, buff=0.3
            )
            t_desc = Text(desc, font_size=11, color=COLOR_MUTED).move_to(
                bar.get_right() + LEFT * 1.8
            )
            tower_vg.add(VGroup(bar, s_tag, t_name, t_desc))

        tower_vg.arrange(UP, buff=0.15).shift(DOWN * 0.5)

        # Animate tower building from bottom to top (Stage 0 -> Stage 5)
        for level in reversed(tower_vg):
            self.play(FadeIn(level, shift=UP * 0.1), run_time=0.35)

        self.wait(1.0)

        # Highlight why we lift from S_2 to S_3
        lift_note = RoundedRectangle(
            corner_radius=0.1,
            width=9.5,
            height=0.9,
            color=COLOR_YELLOW,
            fill_color=COLOR_CARD,
            fill_opacity=0.95,
            stroke_width=2,
        ).to_edge(DOWN, buff=0.4)

        lift_text1 = Text(
            "Pairwise relations (S₂) cannot express cyclic frustration.",
            font_size=13,
            color=COLOR_WHITE,
        ).move_to(lift_note.get_center() + UP * 0.15)
        lift_text2 = Text(
            "An obstruction at level n forces an arity lift to level n+1: No unpriced rewrites.",
            font_size=13,
            color=COLOR_YELLOW,
            weight="BOLD",
        ).move_to(lift_note.get_center() + DOWN * 0.18)

        lift_vg = VGroup(lift_note, lift_text1, lift_text2)
        self.play(
            FadeIn(lift_vg),
            tower_vg[3].animate.set_stroke(color=COLOR_YELLOW, width=3.5),
            run_time=0.8,
        )
        self.wait(2.0)


if __name__ == "__main__":
    print("Run with: manim -qm -s scenes/scene2_sn_tower_construction.py SnTowerConstruction")
