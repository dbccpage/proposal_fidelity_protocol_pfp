"""Scene 1: Symbol Game State Machine & Graph Obstruction Resolution.

Visualizes:
  1. The 8-stage discrete host verification machine (Stages 0 through 7).
  2. The frustrated directed 3-cycle with edge claims (1, 1, 1).
  3. Cycle holonomy calculation: 1 + 1 + 1 = 3 != 0 -> Phi_1 = 3 (Contradiction).
  4. Exact rational coboundary projection repair: claim shifts to -2 -> Phi_1 = 0 (Consistent).
  5. Cryptographic receipt sealing with SHA-256 digest.

Render sample frame:
    manim -qm -s scenes/scene1_symbol_game_state_machine.py SymbolGameStateMachine

AuthorityEffect: None.
Claim Hygiene: Toy 3-cycle model; demonstrates discrete projection repair under declared edge weights.
"""

from __future__ import annotations

import math

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Create,
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

# 3Blue1Brown Dark Theme & Semantic Color Palette
BG_COLOR = "#0f111a"
COLOR_BLUE = "#3498db"
COLOR_TEAL = "#1abc9c"
COLOR_YELLOW = "#f1c40f"
COLOR_RED = "#e74c3c"
COLOR_GREEN = "#2ecc71"
COLOR_WHITE = "#f8f9fa"
COLOR_MUTED = "#7f8c8d"
COLOR_CARD = "#1a1d2e"

config.background_color = BG_COLOR


class SymbolGameStateMachine(Scene):
    """Main animation scene for Scene 1: State Machine & Graph Obstruction Resolution."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------------------
        # Act I: Title & The 8-Stage Machine (0:00 - 0:25)
        # ---------------------------------------------------------------------
        title = Text("The Symbol Game", font_size=38, color=COLOR_WHITE, weight="BOLD")
        subtitle = Text(
            "State Machine & Graph Obstruction Resolution",
            font_size=22,
            color=COLOR_BLUE,
        )
        title_group = VGroup(title, subtitle).arrange(DOWN, buff=0.15).to_edge(UP, buff=0.4)
        self.play(FadeIn(title_group), run_time=1.0)
        self.wait(0.5)

        # Build 8 stage blocks across screen
        stage_names = [
            "0: Envelope",
            "1: Prompt",
            "2: Candidate",
            "3: LLM Turn",
            "4: Score",
            "5: Code Prop",
            "6: Eval Rcpt",
            "7: Elim Rcpt",
        ]
        stages_vg = VGroup()
        box_width = 1.35
        box_height = 0.75

        for i, name in enumerate(stage_names):
            box = RoundedRectangle(
                corner_radius=0.1,
                width=box_width,
                height=box_height,
                color=COLOR_BLUE if i < 4 else COLOR_MUTED,
                fill_color=COLOR_CARD,
                fill_opacity=0.85,
                stroke_width=2,
            )
            label = Text(name, font_size=13, color=COLOR_WHITE).move_to(box)
            stages_vg.add(VGroup(box, label))

        stages_vg.arrange(RIGHT, buff=0.18).scale_to_fit_width(12.5).shift(UP * 1.5)
        stage_header = Text(
            "Eight Discrete Stages of Host Verification",
            font_size=18,
            color=COLOR_YELLOW,
        ).next_to(stages_vg, UP, buff=0.25)

        self.play(FadeIn(stage_header), FadeIn(stages_vg), run_time=1.2)

        # Animate packet token traversing stages 0 -> 3
        packet_token = Dot(color=COLOR_YELLOW, radius=0.12).move_to(stages_vg[0].get_center())
        packet_label = Text("Packet", font_size=11, color=COLOR_YELLOW).next_to(
            packet_token, UP, buff=0.1
        )
        packet_group = VGroup(packet_token, packet_label)
        self.play(FadeIn(packet_group), run_time=0.4)

        for step in range(1, 4):
            target = stages_vg[step].get_center()
            self.play(
                packet_group.animate.move_to(target + UP * 0.05),
                stages_vg[step][0].animate.set_stroke(color=COLOR_YELLOW, width=3),
                run_time=0.4,
            )

        llm_gate_note = Text(
            "Stage 3: Untrusted Model Proposes Edge Claims",
            font_size=16,
            color=COLOR_YELLOW,
        ).next_to(stages_vg, DOWN, buff=0.3)
        self.play(FadeIn(llm_gate_note), run_time=0.6)
        self.wait(1.0)

        # Clear Stage Bar for Graph Visuals
        self.play(
            FadeOut(stages_vg),
            FadeOut(stage_header),
            FadeOut(packet_group),
            FadeOut(llm_gate_note),
            run_time=0.8,
        )

        # ---------------------------------------------------------------------
        # Act II: Frustrated 3-Cycle Graph Obstruction (0:25 - 0:55)
        # ---------------------------------------------------------------------
        graph_title = Text(
            "Directed 3-Cycle: Claims c = (+1, +1, +1)", font_size=24, color=COLOR_WHITE
        )
        graph_title.next_to(title_group, DOWN, buff=0.3)
        self.play(FadeIn(graph_title), run_time=0.6)

        # Coordinates for equilateral triangle
        radius = 1.8
        coords = {
            "a": [0.0, radius * 0.9, 0.0],
            "b": [
                radius * math.cos(math.radians(210)),
                radius * math.sin(math.radians(210)) + 0.1,
                0.0,
            ],
            "c": [
                radius * math.cos(math.radians(330)),
                radius * math.sin(math.radians(330)) + 0.1,
                0.0,
            ],
        }

        # Draw vertices
        nodes_vg = VGroup()
        node_labels_vg = VGroup()
        for name, pt in coords.items():
            circle = Circle(
                radius=0.35,
                color=COLOR_BLUE,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=3,
            )
            circle.move_to(pt)
            lbl = Text(name, font_size=20, color=COLOR_WHITE, weight="BOLD").move_to(pt)
            nodes_vg.add(circle)
            node_labels_vg.add(lbl)

        # Draw directed arrows with edge claims
        edges_data = [
            ("a", "b", "+1", coords["a"], coords["b"]),
            ("b", "c", "+1", coords["b"], coords["c"]),
            ("c", "a", "+1", coords["c"], coords["a"]),
        ]
        arrows_vg = VGroup()
        edge_labels_vg = VGroup()

        for u, v, val, p1, p2 in edges_data:
            arrow = Arrow(
                start=p1,
                end=p2,
                buff=0.42,
                color=COLOR_BLUE,
                stroke_width=4,
                max_tip_length_to_length_ratio=0.18,
            )
            mid = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, 0.0
            normal = [-(p2[1] - p1[1]), p2[0] - p1[0], 0.0]
            norm_len = math.hypot(normal[0], normal[1])
            offset_pt = [
                mid[0] + 0.35 * normal[0] / norm_len,
                mid[1] + 0.35 * normal[1] / norm_len,
                0.0,
            ]
            elbl = Text(f"{u}→{v}: {val}", font_size=15, color=COLOR_YELLOW).move_to(offset_pt)
            arrows_vg.add(arrow)
            edge_labels_vg.add(elbl)

        self.play(FadeIn(nodes_vg), FadeIn(node_labels_vg), run_time=0.8)
        self.play(Create(arrows_vg), FadeIn(edge_labels_vg), run_time=1.0)
        self.wait(0.5)

        # Holonomy Walk Animation
        walk_tracker = Dot(color=COLOR_YELLOW, radius=0.15).move_to(coords["a"])
        self.play(FadeIn(walk_tracker), run_time=0.3)

        holonomy_box = (
            RoundedRectangle(
                corner_radius=0.12,
                width=5.5,
                height=2.0,
                color=COLOR_RED,
                fill_color=COLOR_CARD,
                fill_opacity=0.9,
                stroke_width=2,
            )
            .to_edge(RIGHT, buff=0.8)
            .shift(DOWN * 0.2)
        )

        walk_calc = Text("Cycle Holonomy Sum:", font_size=16, color=COLOR_WHITE).move_to(
            holonomy_box.get_top() + DOWN * 0.3
        )
        calc_eq = Text("1 + 1 + 1 = 3 ≠ 0", font_size=22, color=COLOR_RED, weight="BOLD").next_to(
            walk_calc, DOWN, buff=0.15
        )
        defect_lbl = Text("Primary Obstruction: Φ₁ = 3", font_size=16, color=COLOR_WHITE).next_to(
            calc_eq, DOWN, buff=0.15
        )
        verdict_bad = Text(
            "VERDICT: CONTRADICTION", font_size=18, color=COLOR_RED, weight="BOLD"
        ).next_to(defect_lbl, DOWN, buff=0.15)

        holonomy_card = VGroup(holonomy_box, walk_calc, calc_eq, defect_lbl, verdict_bad)

        # Move tracker a -> b -> c -> a
        self.play(walk_tracker.animate.move_to(coords["b"]), run_time=0.6)
        self.play(walk_tracker.animate.move_to(coords["c"]), run_time=0.6)
        self.play(walk_tracker.animate.move_to(coords["a"]), run_time=0.6)

        # Flash red upon non-zero holonomy
        self.play(
            FadeIn(holonomy_card),
            arrows_vg.animate.set_color(COLOR_RED),
            nodes_vg.animate.set_stroke(color=COLOR_RED),
            run_time=0.8,
        )
        self.wait(1.5)

        # ---------------------------------------------------------------------
        # Act III: Discrete Projection & Exact Rational Repair (0:55 - 1:15)
        # ---------------------------------------------------------------------
        repair_banner = Text(
            "Host Computes Nearest Coboundary: Repair c(c→a) := -2",
            font_size=20,
            color=COLOR_GREEN,
            weight="BOLD",
        ).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(repair_banner), run_time=0.8)

        # Transform edge c->a label to "-2"
        repaired_elbl = Text("c→a: -2", font_size=15, color=COLOR_GREEN).move_to(
            edge_labels_vg[2].get_center()
        )

        # Green holonomy card
        holonomy_box_green = RoundedRectangle(
            corner_radius=0.12,
            width=5.5,
            height=2.0,
            color=COLOR_GREEN,
            fill_color=COLOR_CARD,
            fill_opacity=0.9,
            stroke_width=2,
        ).move_to(holonomy_box)

        calc_eq_repaired = Text(
            "1 + 1 + (-2) = 0", font_size=22, color=COLOR_GREEN, weight="BOLD"
        ).move_to(calc_eq)
        defect_repaired = Text(
            "Primary Obstruction: Φ₁ = 0", font_size=16, color=COLOR_WHITE
        ).move_to(defect_lbl)
        verdict_good = Text(
            "VERDICT: CONSISTENT", font_size=18, color=COLOR_GREEN, weight="BOLD"
        ).move_to(verdict_bad)

        holonomy_card_green = VGroup(
            holonomy_box_green, walk_calc, calc_eq_repaired, defect_repaired, verdict_good
        )

        self.play(
            ReplacementTransform(edge_labels_vg[2], repaired_elbl),
            arrows_vg.animate.set_color(COLOR_GREEN),
            nodes_vg.animate.set_stroke(color=COLOR_GREEN),
            ReplacementTransform(holonomy_card, holonomy_card_green),
            run_time=1.2,
        )

        # Retrace walk
        self.play(walk_tracker.animate.move_to(coords["b"]), run_time=0.5)
        self.play(walk_tracker.animate.move_to(coords["c"]), run_time=0.5)
        self.play(walk_tracker.animate.move_to(coords["a"]), run_time=0.5)
        self.wait(1.0)

        # ---------------------------------------------------------------------
        # Act IV: Sealed Receipt Card (1:15 - 1:30)
        # ---------------------------------------------------------------------
        self.play(
            FadeOut(walk_tracker),
            FadeOut(repair_banner),
            FadeOut(holonomy_card_green),
            FadeOut(arrows_vg),
            FadeOut(edge_labels_vg[0]),
            FadeOut(edge_labels_vg[1]),
            FadeOut(repaired_elbl),
            FadeOut(nodes_vg),
            FadeOut(node_labels_vg),
            FadeOut(graph_title),
            run_time=0.8,
        )

        receipt_box = RoundedRectangle(
            corner_radius=0.15,
            width=8.5,
            height=3.8,
            color=COLOR_TEAL,
            fill_color=COLOR_CARD,
            fill_opacity=0.95,
            stroke_width=2,
        ).move_to(DOWN * 0.3)

        r_title = Text(
            "IMMUTABLE EVALUATION RECEIPT", font_size=20, color=COLOR_TEAL, weight="BOLD"
        )
        r_title.next_to(receipt_box.get_top(), DOWN, buff=0.3)

        r_lines = [
            'schema_version: "core.symbol-game.evaluation-receipt.v1"',
            'status: "ExactRepair"',
            "primary_defect_phi1: 0",
            "cycle_sum: 0",
            'carrier: ["a", "b", "c"]',
            'sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"',
        ]
        r_text_vg = VGroup()
        for line in r_lines:
            r_text_vg.add(Text(line, font_size=13, color=COLOR_WHITE))
        r_text_vg.arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(r_title, DOWN, buff=0.35)

        receipt_vg = VGroup(receipt_box, r_title, r_text_vg)
        self.play(FadeIn(receipt_vg), run_time=1.0)

        claim_fence = Text(
            "Scope: Checked by discrete projection on finite weighted graphs.",
            font_size=13,
            color=COLOR_MUTED,
        ).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(claim_fence), run_time=0.6)
        self.wait(2.0)


if __name__ == "__main__":
    print(
        "Run with: manim -qm -s scenes/scene1_symbol_game_state_machine.py SymbolGameStateMachine"
    )
