use crate::kinds::*;
use crate::schema::*;

impl ConstitutionalBlock {
    pub fn validate(&self) -> Result<(), String> {
        self.validate_forbidden_mixes()?;
        self.validate_contract_dependencies()?;
        self.validate_certificate_requirements()?;
        Ok(())
    }

    fn validate_forbidden_mixes(&self) -> Result<(), String> {
        if self.forbidden_later_layers.contains(&self.authority_layer) {
            return Err("constitution cannot forbid its own authority layer".into());
        }

        let expected = expected_layer_for_family(&self.emits);
        if self.authority_layer != expected {
            return Err(format!(
                "{:?} must use {:?} authority layer",
                self.emits, expected
            ));
        }

        Ok(())
    }

    fn validate_contract_dependencies(&self) -> Result<(), String> {
        if (self.authority_layer == AuthorityLayer::Structure
            || self.authority_layer == AuthorityLayer::Fact)
            && self.contract_dependencies.is_empty()
            && self.law_refs.is_empty()
        {
            return Err(
                "Structure and Fact layers require at least one contract_dependency or law_ref"
                    .into(),
            );
        }
        Ok(())
    }

    fn validate_certificate_requirements(&self) -> Result<(), String> {
        if !self
            .replay_certificates
            .contains(&"schema_hash".to_string())
        {
            return Err("constitution must require 'schema_hash' certificate".into());
        }
        Ok(())
    }
}

fn expected_layer_for_family(family: &ArtifactFamily) -> AuthorityLayer {
    match family {
        ArtifactFamily::StructureArtifact => AuthorityLayer::Structure,
        ArtifactFamily::EvidenceEnvelope => AuthorityLayer::Evidence,
        ArtifactFamily::FactEnvelope => AuthorityLayer::Fact,
        ArtifactFamily::DecisionEnvelope => AuthorityLayer::Judgment,
        ArtifactFamily::ActionLicense => AuthorityLayer::Action,
        ArtifactFamily::Action => AuthorityLayer::Action,
        ArtifactFamily::Record => AuthorityLayer::Record,
    }
}

impl ContractDescriptor {
    pub fn validate(&self) -> Result<(), String> {
        self.validate_common()?;
        if let Some(res) = self.validate_role_artifact_and_eval() {
            return res;
        }
        if let Some(res) = self.validate_role_execution_and_policy() {
            return res;
        }
        if let Some(res) = self.validate_role_runtime_and_search() {
            return res;
        }
        self.validate_role_adapters_and_math()
    }

    fn validate_role_artifact_and_eval(&self) -> Option<Result<(), String>> {
        match self.role {
            ComponentRole::DeclaredActionCandidate => Some(self.validate_declared_action_candidate()),
            ComponentRole::CheckedPacket => Some(self.validate_checked_packet()),
            ComponentRole::Certificate => Some(self.validate_certificate_artifact()),
            ComponentRole::CertificateStore => Some(self.validate_certificate_store()),
            ComponentRole::CertificateApiInterface => Some(self.validate_certificate_api_interface()),
            ComponentRole::Evaluator => Some(self.validate_evaluator()),
            ComponentRole::Validator => Some(self.validate_validator()),
            ComponentRole::Diagnostic => Some(self.validate_diagnostic()),
            _ => None,
        }
    }

    fn validate_role_execution_and_policy(&self) -> Option<Result<(), String>> {
        match self.role {
            ComponentRole::HealthModel => Some(self.validate_health_model()),
            ComponentRole::Observable => Some(self.validate_observable()),
            ComponentRole::Measurement => Some(self.validate_measurement()),
            ComponentRole::Engine => Some(self.validate_engine()),
            ComponentRole::Witness => Some(self.validate_witness()),
            ComponentRole::Policy if self.id == "sentinel.policy" => Some(self.validate_policy()),
            ComponentRole::Policy => Some(Ok(())),
            _ => None,
        }
    }

    fn validate_role_runtime_and_search(&self) -> Option<Result<(), String>> {
        match self.role {
            ComponentRole::Replay => Some(self.validate_replay()),
            ComponentRole::Pipeline => Some(self.validate_pipeline()),
            ComponentRole::LiftLicense => Some(self.validate_lift_license()),
            ComponentRole::Trace => Some(self.validate_trace()),
            ComponentRole::Search => Some(self.validate_search()),
            ComponentRole::Solver => Some(self.validate_solver()),
            ComponentRole::Kernel => Some(self.validate_kernel()),
            _ => None,
        }
    }

    fn validate_role_adapters_and_math(&self) -> Result<(), String> {
        match self.role {
            ComponentRole::LlmAdapter => self.validate_llm_adapter(),
            ComponentRole::SymbolGame => self.validate_symbol_game(),
            ComponentRole::TerminalMapper => self.validate_terminal_mapper(),
            ComponentRole::Terminalizer => self.validate_terminalizer(),
            ComponentRole::AuthInterface => self.validate_auth_interface(),
            ComponentRole::Packetization => self.validate_packetization(),
            ComponentRole::MathObject => self.validate_math_object(),
            ComponentRole::MathComputation => self.validate_math_computation(),
            _ => Ok(()),
        }
    }

    fn validate_common(&self) -> Result<(), String> {
        if self.id.trim().is_empty() {
            return Err("contract id must not be empty".into());
        }
        if self.name.trim().is_empty() {
            return Err("contract name must not be empty".into());
        }
        if let Some(constitution) = &self.constitution {
            constitution
                .validate()
                .map_err(|e| format!("constitution error: {}", e))?;
        }
        Ok(())
    }

    pub fn forbid_capability(&self, cap: Capability, message: &str) -> Result<(), String> {
        if self.capabilities.forbids(cap) {
            Ok(())
        } else {
            Err(message.into())
        }
    }

    fn forbid_capabilities(&self, rules: &[(Capability, &str)]) -> Result<(), String> {
        for &(cap, message) in rules {
            self.forbid_capability(cap, message)?;
        }
        Ok(())
    }

    fn require_constraint_or_license(
        &self,
        flag: Option<bool>,
        license: &str,
        err_msg: &str,
    ) -> Result<(), String> {
        if flag != Some(true) {
            let has_license = self
                .requires
                .as_ref()
                .is_some_and(|r| r.licenses.iter().any(|l| l == license));
            if !has_license {
                return Err(err_msg.into());
            }
        }
        Ok(())
    }

    fn require_constitution(
        &self,
        family: ArtifactFamily,
        layer: AuthorityLayer,
    ) -> Result<(), String> {
        let c = self
            .constitution
            .as_ref()
            .ok_or("contract requires constitution block")?;
        if c.emits != family {
            return Err(format!("contract must emit {:?}", family));
        }
        if c.authority_layer != layer {
            return Err(format!("contract must use {:?} authority layer", layer));
        }
        Ok(())
    }

    fn validate_declared_action_candidate(&self) -> Result<(), String> {
        if self.domain_type.is_none() {
            return Err("DeclaredActionCandidate requires domain_type".into());
        }
        if self.codomain_type.is_none() {
            return Err("DeclaredActionCandidate requires codomain_type".into());
        }
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("DeclaredActionCandidate must have authority_effect = EvidenceOnly".into());
        }

        if self.laws.is_none() {
            return Err("DeclaredActionCandidate requires laws declared as claims".into());
        }

        self.require_constraint_or_license(
            self.constraints.search_forbidden,
            "search",
            "search must be forbidden unless explicitly licensed",
        )?;
        self.require_constraint_or_license(
            self.constraints.hidden_state_forbidden,
            "hidden_state",
            "hidden state must be forbidden unless explicitly licensed",
        )?;
        self.require_constraint_or_license(
            self.constraints.mutation_forbidden,
            "mutation",
            "mutation must be forbidden unless explicitly licensed",
        )?;

        if self.operator_class.is_some() {
            return Err("DeclaredActionCandidate must not declare accepted operator_class; classifier owns E/I/C/R/M".into());
        }

        Ok(())
    }

    fn validate_certificate_artifact(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("certificate must have authority_effect = EvidenceOnly".into());
        }
        self.validate_certificate_constraints()?;
        self.validate_certificate_bindings()?;
        self.forbid_capabilities(&[
            (Capability::Terminalization, "certificate must not terminalize"),
            (Capability::SolverExecution, "certificate must not execute"),
            (
                Capability::PolicyInterpretation,
                "certificate must not interpret policy",
            ),
        ])
    }

    fn validate_certificate_constraints(&self) -> Result<(), String> {
        let checks = [
            (
                self.constraints.immutable_after_emit,
                "certificate must be immutable after emit",
            ),
            (
                self.constraints.mutation_forbidden,
                "certificate must forbid mutation",
            ),
            (
                self.constraints.typed_output_required,
                "certificate must require typed output",
            ),
            (
                self.constraints.signature_required,
                "certificate must require signature",
            ),
            (
                self.constraints.certificate_hash_required,
                "certificate must require certificate hash",
            ),
            (
                self.constraints.policy_hash_required,
                "certificate must require policy hash",
            ),
            (
                self.constraints.policy_version_required,
                "certificate must bind policy version",
            ),
            (
                self.constraints.request_hash_required,
                "certificate must require request hash",
            ),
            (
                self.constraints.replay_required,
                "certificate must require replay",
            ),
        ];
        for (flag, msg) in checks {
            if flag != Some(true) {
                return Err(msg.into());
            }
        }
        Ok(())
    }

    fn validate_certificate_bindings(&self) -> Result<(), String> {
        if self.replay.as_ref().is_none_or(|r| r.required.is_empty()) {
            return Err("certificate must declare replay block".into());
        }
        if self
            .witnesses
            .as_ref()
            .is_none_or(|w| w.required.is_empty())
        {
            return Err("certificate must declare witness requirements".into());
        }
        Ok(())
    }

    fn validate_evaluator(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::DecisionEnvelope, AuthorityLayer::Judgment)?;
        if self.authority_effect != ContractEffect::RequestsDecision {
            return Err("evaluator must have authority_effect = RequestsDecision".into());
        }
        if self.subject_type.is_none() {
            return Err("evaluator requires subject_type".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("evaluator must forbid mutation".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("evaluator must emit typed evaluation result".into());
        }
        if self.constraints.runtime_orchestration_forbidden != Some(true) {
            return Err("evaluator must not orchestrate runtime".into());
        }
        if self.evaluates_outputs_of.is_some() {
            return Err(
                "evaluator must not declare evaluates_outputs_of; policy owns admissibility".into(),
            );
        }
        self.forbid_capability(Capability::ComputePhi, "evaluator must not recompute phi")?;
        self.forbid_capability(
            Capability::ComputeGamma,
            "evaluator must not recompute gamma",
        )?;
        Ok(())
    }

    fn validate_validator(&self) -> Result<(), String> {
        if self.authority_effect == ContractEffect::FactOnly
            && self.constraints.checker_boundary_required != Some(true)
        {
            return Err("FactOnly validator requires checker boundary".into());
        }
        if self.authority_effect != ContractEffect::EvidenceOnly
            && self.authority_effect != ContractEffect::FactOnly
        {
            return Err("validator must be EvidenceOnly or scoped FactOnly".into());
        }
        if self.subject_type.is_none() {
            return Err("validator unit requires subject_type".into());
        }
        if self.constraints.read_only != Some(true) {
            return Err("validator must be read-only".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("validator must forbid mutation".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("validator must require typed output".into());
        }
        Ok(())
    }

    fn validate_checked_packet(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::FactEnvelope, AuthorityLayer::Fact)?;
        if self.authority_effect != ContractEffect::FactOnly {
            return Err("checked packet must have authority_effect = FactOnly".into());
        }
        if self.constraints.checker_boundary_required != Some(true) {
            return Err("checked packet requires checker boundary".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("checked packet must forbid mutation".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("checked packet must require typed output".into());
        }
        Ok(())
    }

    fn validate_diagnostic(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("diagnostic must have authority_effect = EvidenceOnly".into());
        }
        Ok(())
    }

    fn validate_observable(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("observable must have authority_effect = EvidenceOnly".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("observable must forbid mutation".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("observable must require typed output".into());
        }
        if self.constraints.runtime_orchestration_forbidden != Some(true) {
            return Err("observable must not orchestrate runtime".into());
        }
        Ok(())
    }

    fn validate_measurement(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("measurement must have authority_effect = EvidenceOnly".into());
        }
        if self.subject_type.is_none() {
            return Err("measurement requires subject_type".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("measurement must forbid mutation".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("measurement must require typed output".into());
        }
        if self.constraints.operator_execution_forbidden != Some(true) {
            return Err("measurement must forbid operator execution".into());
        }
        if self.constraints.runtime_orchestration_forbidden != Some(true) {
            return Err("measurement must not orchestrate runtime".into());
        }
        Ok(())
    }

    fn validate_health_model(&self) -> Result<(), String> {
        // Per 06_execution.yaml: health_model has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("health model must have authority_effect = EvidenceOnly".into());
        }
        Ok(())
    }

    fn validate_engine(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::Action, AuthorityLayer::Action)?;
        if self.authority_effect != ContractEffect::StateTransition {
            return Err("engine must have authority_effect = StateTransition".into());
        }
        let laws = self.laws.as_ref().ok_or("engine requires laws")?;
        if laws.effect != LawPresence::Required(EffectLawDecl::Stateful) {
            return Err("engine must have effect=Stateful".into());
        }
        if self.runtime_state_type.is_none() {
            return Err("engine requires runtime_state_type".into());
        }
        if self.constraints.iteration_forbidden == Some(true) {
            return Err("engine must allow iteration".into());
        }
        if self.constraints.action_license_required != Some(true) {
            return Err(
                "engine must require action license (ActionLicense) before StateTransition".into(),
            );
        }
        self.forbid_capabilities(&[
            (Capability::ComputePhi, "engine must not compute phi"),
            (Capability::ComputeGamma, "engine must not compute gamma"),
            (
                Capability::PolicyInterpretation,
                "engine must not run policy interpreter or evaluate policy internally",
            ),
            (Capability::Evaluation, "engine must not evaluate"),
            (
                Capability::CertificateSigning,
                "engine must not sign certificates",
            ),
            (
                Capability::EmitCertificate,
                "engine must not emit certificates",
            ),
        ])
    }

    fn validate_certificate_store(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::None {
            return Err("certificate store must have authority_effect = None".into());
        }
        if self.constraints.immutable_after_emit != Some(true) {
            return Err("certificate store must be immutable after emit".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("certificate store must forbid mutation".into());
        }
        if self.constraints.raw_payload_forbidden != Some(true) {
            return Err("certificate store must forbid raw payload exposure".into());
        }
        self.forbid_capability(
            Capability::RuntimeMutation,
            "certificate store must not overwrite certificates",
        )?;
        self.forbid_capability(
            Capability::CertificateSigning,
            "certificate store must not sign certificates",
        )?;
        Ok(())
    }

    fn validate_witness(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("witness must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(Capability::CertificateSigning, "witness must not authorize")?;
        self.forbid_capability(
            Capability::PolicyInterpretation,
            "witness must not make admissibility decisions",
        )?;
        self.forbid_capability(Capability::Terminalization, "witness must not terminalize")?;
        Ok(())
    }

    fn validate_policy(&self) -> Result<(), String> {
        if self.id == "sentinel.policy" {
            self.require_constitution(ArtifactFamily::DecisionEnvelope, AuthorityLayer::Judgment)?;
        }
        if self.authority_effect != ContractEffect::RequestsDecision {
            return Err("policy must have authority_effect = RequestsDecision".into());
        }
        if self.constraints.deterministic != Some(true) {
            return Err("policy must be deterministic".into());
        }
        if self.constraints.hidden_state_forbidden != Some(true) {
            return Err("policy must forbid hidden state".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("policy must forbid mutation".into());
        }
        if self.constraints.runtime_orchestration_forbidden != Some(true) {
            return Err("policy must not orchestrate runtime".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("policy must require typed output".into());
        }
        if self.constraints.policy_version_required != Some(true) {
            return Err("policy must require policy version".into());
        }
        self.forbid_capabilities(&[
            (Capability::ComputePhi, "policy must not compute metrics"),
            (Capability::ComputeGamma, "policy must not compute gamma"),
            (
                Capability::ComputeRefusalSignal,
                "policy must not compute refusal signal",
            ),
            (Capability::SolverExecution, "policy must not call solvers"),
            (Capability::Terminalization, "policy must not terminalize"),
        ])
    }

    fn validate_replay(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("replay must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(
            Capability::RuntimeMutation,
            "replay must not mutate trace bundle",
        )?;
        self.forbid_capability(Capability::Terminalization, "replay must not terminalize")?;
        Ok(())
    }

    fn validate_pipeline(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::None {
            return Err("pipeline must have authority_effect = None".into());
        }
        self.forbid_capability(
            Capability::CertificateSigning,
            "pipeline must not sign certificates",
        )?;
        self.forbid_capability(
            Capability::RuntimeMutation,
            "pipeline must not mutate store",
        )?;
        Ok(())
    }

    fn validate_lift_license(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::ActionLicense, AuthorityLayer::Action)?;
        // Per 08_lifts.yaml: lift_license has authority_effect = AuthorizesTransition
        if self.authority_effect != ContractEffect::AuthorizesTransition {
            return Err("lift license must have authority_effect = AuthorizesTransition".into());
        }
        if self.constraints.scope_bound != Some(true) {
            return Err("lift license must be scope bound".into());
        }
        if self.constraints.non_transferable != Some(true) {
            return Err("lift license must be non-transferable".into());
        }
        if self.constraints.authority_does_not_exceed_evidence != Some(true) {
            return Err("lift license authority must not exceed evidence".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("lift license must forbid mutation".into());
        }
        if self.replay.as_ref().is_none_or(|r| r.required.is_empty()) {
            return Err("lift license must declare replay block".into());
        }
        if self
            .witnesses
            .as_ref()
            .is_none_or(|w| w.required.is_empty())
        {
            return Err("lift license must declare witness requirements".into());
        }
        self.forbid_capabilities(&[
            (
                Capability::ExecuteStateTransition,
                "lift license must not execute state transitions",
            ),
            (
                Capability::RuntimeMutation,
                "lift license must not mutate runtime",
            ),
        ])
    }

    fn validate_trace(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence)?;
        // Per 02_evidence.yaml: trace has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("trace must have authority_effect = EvidenceOnly".into());
        }
        if self.constraints.immutable_after_emit != Some(true) {
            return Err("trace must be immutable after emit".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("trace must forbid mutation".into());
        }
        Ok(())
    }

    fn validate_search(&self) -> Result<(), String> {
        // Per 06_execution.yaml: search_kernel has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("search must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(Capability::Terminalization, "search must not terminalize")?;
        self.forbid_capability(
            Capability::CertificateSigning,
            "search must not sign certificates",
        )?;
        self.forbid_capability(Capability::Evaluation, "search must not evaluate")?;
        Ok(())
    }

    fn validate_solver(&self) -> Result<(), String> {
        // Per 06_execution.yaml: solver_kernel has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("solver must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(Capability::Terminalization, "solver must not terminalize")?;
        self.forbid_capability(
            Capability::CertificateSigning,
            "solver must not sign certificates",
        )?;
        self.forbid_capability(Capability::Evaluation, "solver must not evaluate")?;
        Ok(())
    }

    fn validate_kernel(&self) -> Result<(), String> {
        // Per 06_execution.yaml: kernel has authority_effect = None
        if self.authority_effect != ContractEffect::None {
            return Err("kernel must have authority_effect = None".into());
        }
        self.forbid_capability(
            Capability::CertificateSigning,
            "kernel must not sign certificates",
        )?;
        Ok(())
    }

    fn validate_llm_adapter(&self) -> Result<(), String> {
        // Per 07_products.yaml: llm_adapter has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("llm adapter must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(
            Capability::CertificateSigning,
            "llm adapter must not sign certificates",
        )?;
        self.forbid_capability(
            Capability::Terminalization,
            "llm adapter must not terminalize",
        )?;
        self.forbid_capability(Capability::Evaluation, "llm adapter must not evaluate")?;
        self.forbid_capability(Capability::Validation, "llm adapter must not validate")?;
        Ok(())
    }

    fn validate_symbol_game(&self) -> Result<(), String> {
        // Per 07_products.yaml: symbol_game has authority_effect = EvidenceOnly
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("symbol game must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(
            Capability::CertificateSigning,
            "symbol game must not sign certificates",
        )?;
        self.forbid_capability(
            Capability::Terminalization,
            "symbol game must not terminalize",
        )?;
        Ok(())
    }

    fn validate_terminal_mapper(&self) -> Result<(), String> {
        self.require_constitution(ArtifactFamily::DecisionEnvelope, AuthorityLayer::Judgment)?;
        if self.authority_effect != ContractEffect::RequestsDecision {
            return Err("terminal mapper must have authority_effect = RequestsDecision".into());
        }
        if self.constraints.typed_output_required != Some(true) {
            return Err("terminal mapper must require typed output".into());
        }
        self.forbid_capabilities(&[
            (
                Capability::ExecuteStateTransition,
                "terminal mapper must not execute",
            ),
            (
                Capability::ActionLicensing,
                "terminal mapper must not license actions",
            ),
            (
                Capability::MeasurementComputation,
                "terminal mapper must not compute measurements",
            ),
            (
                Capability::CertificateSigning,
                "terminal mapper must not certify",
            ),
            (
                Capability::RuntimeMutation,
                "terminal mapper must not mutate",
            ),
            (
                Capability::ComputePhi,
                "terminal mapper must not compute phi",
            ),
            (
                Capability::ComputeGamma,
                "terminal mapper must not compute gamma",
            ),
        ])
    }

    fn validate_terminalizer(&self) -> Result<(), String> {
        if self.status == ContractStatus::Deprecated {
            return Ok(());
        }
        Err("Terminalizer is deprecated; use TerminalMapper".into())
    }

    fn validate_certificate_api_interface(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::None {
            return Err("certificate api interface must have authority_effect = None".into());
        }
        if self.constraints.read_only != Some(true) {
            return Err("certificate api interface must be read-only".into());
        }
        if self.constraints.mutation_forbidden != Some(true) {
            return Err("certificate api interface must forbid mutation".into());
        }
        if self.constraints.raw_payload_forbidden != Some(true) {
            return Err("certificate api interface must forbid raw payload exposure".into());
        }
        if self.constraints.public_signing_forbidden != Some(true) {
            return Err("certificate api interface must forbid public signing".into());
        }
        self.forbid_capabilities(&[
            (
                Capability::CertificateSigning,
                "certificate api interface must not sign certificates",
            ),
            (
                Capability::EmitCertificate,
                "certificate api interface must not emit certificates",
            ),
            (
                Capability::Evaluation,
                "certificate api interface must not evaluate",
            ),
            (
                Capability::Terminalization,
                "certificate api interface must not terminalize",
            ),
            (
                Capability::AuthorityPromotion,
                "certificate api interface must not promote authority",
            ),
            (
                Capability::RuntimeMutation,
                "certificate api interface must not mutate store",
            ),
        ])
    }

    fn validate_packetization(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::EvidenceOnly {
            return Err("packetization must have authority_effect = EvidenceOnly".into());
        }
        self.forbid_capability(
            Capability::SemanticTruthClaim,
            "packetization must not certify semantic truth",
        )?;
        Ok(())
    }

    fn validate_math_object(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::None
            && self.authority_effect != ContractEffect::EvidenceOnly
        {
            return Err("math object must be None or EvidenceOnly".into());
        }
        self.forbid_capability(Capability::EmitDecision, "math object must not decide")?;
        self.forbid_capability(
            Capability::EmitCertificate,
            "math object must not emit certificates",
        )?;
        self.forbid_capability(Capability::EmitAction, "math object must not emit actions")?;
        Ok(())
    }

    fn validate_math_computation(&self) -> Result<(), String> {
        if self.authority_effect != ContractEffect::EvidenceOnly
            && self.authority_effect != ContractEffect::FactOnly
        {
            return Err("math computation must be EvidenceOnly or scoped FactOnly".into());
        }
        self.forbid_capability(Capability::EmitDecision, "math computation must not decide")?;
        self.forbid_capability(
            Capability::EmitCertificate,
            "math computation must not emit certificates",
        )?;
        self.forbid_capability(
            Capability::EmitAction,
            "math computation must not emit actions",
        )?;
        Ok(())
    }

    fn validate_auth_interface(&self) -> Result<(), String> {
        // Per 05_governance.yaml: auth_interface has authority_effect = None
        if self.authority_effect != ContractEffect::None {
            return Err("auth interface must have authority_effect = None".into());
        }
        self.forbid_capability(
            Capability::CertificateSigning,
            "auth interface must not sign certificates",
        )?;
        self.forbid_capability(
            Capability::Terminalization,
            "auth interface must not terminalize",
        )?;
        Ok(())
    }
}

pub fn validate_registry(contracts: &[ContractDescriptor]) -> Result<(), String> {
    use std::collections::HashSet;

    let mut ids = HashSet::new();

    for c in contracts {
        c.validate()
            .map_err(|e| format!("contract '{}' failed validation: {}", c.id, e))?;

        if !ids.insert(&c.id) {
            return Err(format!("duplicate contract id: {}", c.id));
        }
    }

    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/validate.rs
// Claim: urn:core:crates_rs:core-contracts:validate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord399692a5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord399692a5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError399692a5 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError399692a5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError399692a5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError399692a5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord399692a5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError399692a5> {
        if capacity_bound == 0 {
            return Err(BoundaryError399692a5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError399692a5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError399692a5::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod constitution_tests {
    //! Negative controls for `ConstitutionalBlock::validate`.
    //!
    //! Role-level validators (certificate, engine, policy, witness, …) are covered
    //! from `core_contracts::descriptors::product_spine`, which owns the concrete
    //! descriptor fixtures. `ConstitutionalBlock` needs no such fixture, so its
    //! failure paths are pinned here, at the lowest tier that can witness them.
    use super::*;

    /// A constitution that satisfies every rule. Each test breaks exactly one thing,
    /// so a failure names the rule it broke.
    fn valid(emits: ArtifactFamily, authority_layer: AuthorityLayer) -> ConstitutionalBlock {
        ConstitutionalBlock {
            contract_dependencies: vec!["sentinel.some.dependency".to_string()],
            law_refs: vec![],
            emits,
            authority_layer,
            forbidden_later_layers: vec![],
            replay_certificates: vec!["schema_hash".to_string()],
        }
    }

    /// The family -> layer map `expected_layer_for_family` is required to implement.
    /// This is the expected-value oracle, not a reimplementation: every assertion
    /// below runs against the production `validate()` path.
    fn expected_family_layers() -> Vec<(ArtifactFamily, AuthorityLayer)> {
        vec![
            (ArtifactFamily::StructureArtifact, AuthorityLayer::Structure),
            (ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence),
            (ArtifactFamily::FactEnvelope, AuthorityLayer::Fact),
            (ArtifactFamily::DecisionEnvelope, AuthorityLayer::Judgment),
            (ArtifactFamily::ActionLicense, AuthorityLayer::Action),
            (ArtifactFamily::Action, AuthorityLayer::Action),
            (ArtifactFamily::Record, AuthorityLayer::Record),
        ]
    }

    #[test]
    fn baseline_constitution_validates() {
        let c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        assert_eq!(c.validate(), Ok(()));
    }

    #[test]
    fn constitution_forbidding_its_own_authority_layer_rejected() {
        let mut c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        c.forbidden_later_layers = vec![AuthorityLayer::Evidence];
        assert_eq!(
            c.validate()
                .expect_err("self-forbidding constitution must be rejected"),
            "constitution cannot forbid its own authority layer"
        );
    }

    #[test]
    fn forbidding_a_different_layer_is_permitted() {
        // Discriminates the rule above from "forbidden_later_layers must be empty".
        let mut c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        c.forbidden_later_layers = vec![AuthorityLayer::Action];
        assert_eq!(c.validate(), Ok(()));
    }

    /// Class 1: pins all seven arms of the family -> layer map in one law.
    #[test]
    fn every_artifact_family_validates_at_its_expected_layer() {
        let pairs = expected_family_layers();
        assert_eq!(
            pairs.len(),
            7,
            "ArtifactFamily variant count changed; extend expected_family_layers"
        );
        for (family, layer) in pairs {
            let c = valid(family.clone(), layer.clone());
            assert_eq!(
                c.validate(),
                Ok(()),
                "family {family:?} must validate at its expected layer {layer:?}"
            );
        }
    }

    /// Class 1 dual: no family may validate at a layer that is not its expected one.
    /// `Runtime` is never an expected layer, so it is wrong for every family.
    #[test]
    fn no_artifact_family_validates_at_the_runtime_layer() {
        for (family, expected) in expected_family_layers() {
            let c = valid(family.clone(), AuthorityLayer::Runtime);
            assert_eq!(
                c.validate()
                    .expect_err(&format!("family {family:?} must reject the Runtime layer")),
                format!("{family:?} must use {expected:?} authority layer"),
            );
        }
    }

    #[test]
    fn structure_layer_without_dependency_or_law_ref_rejected() {
        let mut c = valid(ArtifactFamily::StructureArtifact, AuthorityLayer::Structure);
        c.contract_dependencies.clear();
        c.law_refs.clear();
        assert_eq!(
            c.validate()
                .expect_err("ungrounded Structure layer must be rejected"),
            "Structure and Fact layers require at least one contract_dependency or law_ref"
        );
    }

    #[test]
    fn fact_layer_without_dependency_or_law_ref_rejected() {
        let mut c = valid(ArtifactFamily::FactEnvelope, AuthorityLayer::Fact);
        c.contract_dependencies.clear();
        c.law_refs.clear();
        assert_eq!(
            c.validate()
                .expect_err("ungrounded Fact layer must be rejected"),
            "Structure and Fact layers require at least one contract_dependency or law_ref"
        );
    }

    #[test]
    fn law_ref_alone_grounds_a_fact_layer() {
        // Pins the `||` branch: a law_ref substitutes for a contract_dependency.
        let mut c = valid(ArtifactFamily::FactEnvelope, AuthorityLayer::Fact);
        c.contract_dependencies.clear();
        c.law_refs = vec!["sentinel.law.some_law".to_string()];
        assert_eq!(c.validate(), Ok(()));
    }

    #[test]
    fn evidence_layer_needs_no_dependency_or_law_ref() {
        // The grounding rule is scoped to Structure and Fact only.
        let mut c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        c.contract_dependencies.clear();
        c.law_refs.clear();
        assert_eq!(c.validate(), Ok(()));
    }

    #[test]
    fn constitution_without_schema_hash_certificate_rejected() {
        let mut c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        c.replay_certificates = vec!["policy_hash".to_string()];
        assert_eq!(
            c.validate()
                .expect_err("missing schema_hash certificate must be rejected"),
            "constitution must require 'schema_hash' certificate"
        );
    }

    #[test]
    fn empty_replay_certificates_rejected() {
        let mut c = valid(ArtifactFamily::EvidenceEnvelope, AuthorityLayer::Evidence);
        c.replay_certificates.clear();
        assert_eq!(
            c.validate()
                .expect_err("empty replay_certificates must be rejected"),
            "constitution must require 'schema_hash' certificate"
        );
    }
}

#[cfg(test)]
mod descriptor_tests {
    //! Fixture builder + negative-control matrix for `ContractDescriptor`.
    //!
    //! `ContractDescriptor` has ~30 fields and no `Default`, which is why these
    //! branches were never pinned. `bare()` supplies the empty shape; each test
    //! perturbs exactly one field, so a failure names the rule it broke.
    //!
    //! Role validators reachable from concrete product descriptors are covered in
    //! `core_contracts::descriptors::product_spine`. Covered here are the branches
    //! that crate's fixtures never reach: the lift-license authority boundary,
    //! registry duplicate-id, and the Terminalizer deprecation gate.
    use super::*;

    /// Everything empty. Not valid for most roles — callers fill in what their
    /// validator reads. This is a fixture, not a reimplementation of `validate()`.
    fn bare(role: ComponentRole, authority_effect: ContractEffect) -> ContractDescriptor {
        ContractDescriptor {
            id: "sentinel.test.subject".to_string(),
            name: "test subject".to_string(),
            category: ContractCategory::Lifts,
            role,
            status: ContractStatus::Canonical,
            authority_effect,
            domain_type: None,
            codomain_type: None,
            subject_type: None,
            runtime_state_type: None,
            laws: None,
            constraints: ConstraintBlock::default(),
            capabilities: CapabilityPolicy::default(),
            requires: None,
            validation: None,
            witnesses: None,
            replay: None,
            constitution: None,
            schema_hash: None,
            algebra_laws: None,
            governed_algebra_layer: None,
            operator_class: None,
            signature: None,
            uros: None,
            evaluates_outputs_of: None,
            decision_scope: None,
            evidence_ceiling: None,
            runtime_enforcement: false,
            proof_obligations: Vec::new(),
            terminals: TerminalPolicy::default(),
            refusals: RefusalPolicy::default(),
            operator_classes: OperatorClassPolicy::default(),
            rust_binding: None,
        }
    }

    /// A lift license that satisfies every clause of `validate_lift_license`.
    fn valid_lift_license() -> ContractDescriptor {
        let mut d = bare(
            ComponentRole::LiftLicense,
            ContractEffect::AuthorizesTransition,
        );
        d.constitution = Some(ConstitutionalBlock {
            contract_dependencies: vec!["sentinel.some.dependency".to_string()],
            law_refs: vec![],
            emits: ArtifactFamily::ActionLicense,
            authority_layer: AuthorityLayer::Action,
            forbidden_later_layers: vec![],
            replay_certificates: vec!["schema_hash".to_string()],
        });
        d.constraints.scope_bound = Some(true);
        d.constraints.non_transferable = Some(true);
        d.constraints.authority_does_not_exceed_evidence = Some(true);
        d.constraints.mutation_forbidden = Some(true);
        d.replay = Some(ReplayBlock {
            required: vec!["schema_hash".to_string()],
        });
        d.witnesses = Some(WitnessesBlock {
            required: vec!["operator_signature".to_string()],
        });
        d.capabilities.forbidden = vec![
            Capability::ExecuteStateTransition,
            Capability::RuntimeMutation,
        ];
        d
    }

    #[test]
    fn valid_lift_license_accepted() {
        assert_eq!(valid_lift_license().validate(), Ok(()));
    }

    // ── the authority-promotion boundary: each clause, its own reason ──────────

    #[test]
    fn lift_license_without_constitution_rejected() {
        let mut d = valid_lift_license();
        d.constitution = None;
        assert_eq!(
            d.validate().expect_err("lift license needs a constitution"),
            "contract requires constitution block"
        );
    }

    #[test]
    fn lift_license_emitting_wrong_family_rejected() {
        let mut d = valid_lift_license();
        // `Action` also maps to the Action layer, so the constitution stays
        // self-consistent and the failure is the family mismatch, not the layer.
        d.constitution.as_mut().unwrap().emits = ArtifactFamily::Action;
        assert_eq!(
            d.validate()
                .expect_err("lift license must emit ActionLicense"),
            "contract must emit ActionLicense"
        );
    }

    #[test]
    fn lift_license_with_wrong_authority_effect_rejected() {
        let mut d = valid_lift_license();
        d.authority_effect = ContractEffect::EvidenceOnly;
        assert_eq!(
            d.validate()
                .expect_err("lift license must authorize transitions"),
            "lift license must have authority_effect = AuthorizesTransition"
        );
    }

    #[test]
    fn lift_license_without_scope_bound_rejected() {
        let mut d = valid_lift_license();
        d.constraints.scope_bound = None;
        assert_eq!(
            d.validate()
                .expect_err("unscoped lift license must be rejected"),
            "lift license must be scope bound"
        );
    }

    #[test]
    fn lift_license_without_non_transferable_rejected() {
        let mut d = valid_lift_license();
        d.constraints.non_transferable = Some(false);
        assert_eq!(
            d.validate()
                .expect_err("transferable lift license must be rejected"),
            "lift license must be non-transferable"
        );
    }

    #[test]
    fn lift_license_with_authority_exceeding_evidence_rejected() {
        let mut d = valid_lift_license();
        d.constraints.authority_does_not_exceed_evidence = None;
        assert_eq!(
            d.validate()
                .expect_err("authority exceeding evidence must be rejected"),
            "lift license authority must not exceed evidence"
        );
    }

    #[test]
    fn lift_license_without_mutation_forbidden_rejected() {
        let mut d = valid_lift_license();
        d.constraints.mutation_forbidden = None;
        assert_eq!(
            d.validate()
                .expect_err("mutating lift license must be rejected"),
            "lift license must forbid mutation"
        );
    }

    #[test]
    fn lift_license_without_replay_block_rejected() {
        let mut d = valid_lift_license();
        d.replay = None;
        assert_eq!(
            d.validate().expect_err("lift license needs a replay block"),
            "lift license must declare replay block"
        );
    }

    #[test]
    fn lift_license_with_empty_replay_required_rejected() {
        // Distinct from the None case: a present-but-empty block is still no replay.
        let mut d = valid_lift_license();
        d.replay = Some(ReplayBlock { required: vec![] });
        assert_eq!(
            d.validate()
                .expect_err("empty replay block must be rejected"),
            "lift license must declare replay block"
        );
    }

    #[test]
    fn lift_license_without_witnesses_rejected() {
        let mut d = valid_lift_license();
        d.witnesses = None;
        assert_eq!(
            d.validate().expect_err("lift license needs witnesses"),
            "lift license must declare witness requirements"
        );
    }

    #[test]
    fn lift_license_with_empty_witnesses_rejected() {
        let mut d = valid_lift_license();
        d.witnesses = Some(WitnessesBlock { required: vec![] });
        assert_eq!(
            d.validate()
                .expect_err("empty witness block must be rejected"),
            "lift license must declare witness requirements"
        );
    }

    #[test]
    fn lift_license_permitting_state_transition_rejected() {
        let mut d = valid_lift_license();
        d.capabilities
            .forbidden
            .retain(|c| *c != Capability::ExecuteStateTransition);
        assert_eq!(
            d.validate()
                .expect_err("a license that may execute is not a license"),
            "lift license must not execute state transitions"
        );
    }

    #[test]
    fn lift_license_permitting_runtime_mutation_rejected() {
        let mut d = valid_lift_license();
        d.capabilities
            .forbidden
            .retain(|c| *c != Capability::RuntimeMutation);
        assert_eq!(
            d.validate()
                .expect_err("lift license must not mutate runtime"),
            "lift license must not mutate runtime"
        );
    }

    // ── registry-level invariant ──────────────────────────────────────────────

    /// A role whose validator is the no-op arm, so registry behaviour is isolated
    /// from role behaviour. `Policy` only validates when id == "sentinel.policy".
    fn registry_member(id: &str) -> ContractDescriptor {
        let mut d = bare(ComponentRole::Policy, ContractEffect::None);
        d.id = id.to_string();
        d
    }

    #[test]
    fn validate_registry_accepts_distinct_ids() {
        let members = vec![registry_member("sentinel.a"), registry_member("sentinel.b")];
        assert_eq!(validate_registry(&members), Ok(()));
    }

    #[test]
    fn validate_registry_rejects_duplicate_ids() {
        let members = vec![
            registry_member("sentinel.a"),
            registry_member("sentinel.b"),
            registry_member("sentinel.a"),
        ];
        assert_eq!(
            validate_registry(&members).expect_err("duplicate ids must be rejected"),
            "duplicate contract id: sentinel.a"
        );
    }

    #[test]
    fn validate_registry_reports_the_failing_member_by_id() {
        let mut bad = registry_member("sentinel.broken");
        bad.name = "  ".to_string();
        assert_eq!(
            validate_registry(&[bad]).expect_err("blank name must be rejected"),
            "contract 'sentinel.broken' failed validation: contract name must not be empty"
        );
    }

    // ── deprecation gate ──────────────────────────────────────────────────────

    #[test]
    fn canonical_terminalizer_rejected() {
        let d = bare(ComponentRole::Terminalizer, ContractEffect::None);
        assert_eq!(
            d.validate()
                .expect_err("live Terminalizer must be rejected"),
            "Terminalizer is deprecated; use TerminalMapper"
        );
    }

    #[test]
    fn deprecated_terminalizer_accepted() {
        let mut d = bare(ComponentRole::Terminalizer, ContractEffect::None);
        d.status = ContractStatus::Deprecated;
        assert_eq!(d.validate(), Ok(()));
    }
}

#[cfg(test)]
mod l4_boundary_tests_399692a5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord399692a5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord399692a5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord399692a5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord399692a5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord399692a5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError399692a5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError399692a5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
