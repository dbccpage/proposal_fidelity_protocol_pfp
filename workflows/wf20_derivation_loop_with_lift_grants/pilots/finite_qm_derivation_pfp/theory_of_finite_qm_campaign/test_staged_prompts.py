import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
prepare=module('prepare_stage')
audit=module('validate_prompts')
PROMPTS=sorted((ROOT/'dag/prompts').glob('*.yaml'))


class StagedPromptTests(unittest.TestCase):
    def reviewed_fixture(self,directory):
        """Synthetic protocol fixture, not a mathematical review receipt."""
        prompt=prepare.load(PROMPTS[0]); collection=prepare.load((PROMPTS[0].parent/prompt['operad_record']).resolve())
        source=HERE/'prepare_stage.py'
        slots={
            prepare.SLOTS[0]:{'mining_status':'FILLED','carrier':'Int','coefficient_ring':'Z','source_pins':[{'path':str(source),'sha256':prepare.digest(source.read_bytes())}],'assumptions':[],'public_input':{}},
            prepare.SLOTS[1]:{'mining_status':'FILLED','operations':[{'catalog_id':'fixture:add','inputs':['Int','Int'],'output':'Int','semantic_predicate':'integer addition'}],'composition_plan':['add(x,0)']},
            prepare.SLOTS[2]:{'mining_status':'FILLED','algebraic_relations':['x+0=x'],'rejection_predicates':['integer equality'],'negative_control_plan':['change the sign; retain a valid control']},
            prepare.SLOTS[3]:{'mining_status':'FILLED','certificate_predicates':['integer equality'],'anchors':['synthetic protocol fixture only'],'unpaid_imports':[]},
        }
        data={'original_target':collection['target']['source_statement'],'work_unit':{'schema_id':'omega.pfp.finite-qm-work-unit.v1','task_id':prompt['node_id'],'objective':'Synthetic protocol test only','selected_catalog_ids':['fixture:add'],'operad_slots':slots,'answer_schema':{'type':'integer'},'checker_id':'fixture:integer-equality'},'catalog':{'entries':[{'id':'fixture:add','inputs':['Int','Int'],'output':'Int'}]}}
        reviewed=Path(directory)/'reviewed.json';review=Path(directory)/'review.json'
        reviewed.write_text(json.dumps(data),encoding='utf-8')
        review.write_text(json.dumps({'task_id':prompt['node_id'],'review_status':'accepted_for_next_step','reviewed_sha256':prepare.digest(reviewed.read_bytes())}),encoding='utf-8')
        return reviewed,review

    def test_all_177_have_consistent_source_collections_and_no_old_contract(self):
        self.assertEqual(audit.validate()['errors'],[])

    def test_every_prompt_prepares_p0_with_target_specific_collection(self):
        for prompt in PROMPTS:
            packet=prepare.build_packet(prompt,attempt_id='mining-first')
            self.assertEqual(packet['stage_id'],'P0_MINE_OPERAD')
            self.assertEqual(packet['task_id'],packet['public_context']['operad_collection']['node_id'])
            self.assertIn('operad_delta',packet['response_contract']['stage']['required'])
            self.assertEqual(packet['dispatch_status'],'prepared_only_no_provider_or_checker_executed')

    def test_every_prompt_refuses_derivation_without_reviewed_missions(self):
        for prompt in PROMPTS:
            with self.assertRaisesRegex(ValueError,'reviewed_missions'):
                prepare.build_packet(prompt,'P1_DERIVE',attempt_id='skip-mining')

    def test_host_verify_and_record_are_not_model_dispatches(self):
        for stage in ('P2_VERIFY','P5_RECORD'):
            with self.assertRaisesRegex(ValueError,'host_stage'):
                prepare.build_packet(PROMPTS[0],stage,attempt_id='host')

    def test_stale_review_and_mismatched_task_are_refused(self):
        prompt=prepare.load(PROMPTS[0]); collection=prepare.load((PROMPTS[0].parent/prompt['operad_record']).resolve())
        with tempfile.TemporaryDirectory() as directory:
            reviewed=Path(directory)/'reviewed.json'; review=Path(directory)/'review.json'
            reviewed.write_text('{}',encoding='utf-8')
            review.write_text(json.dumps({'task_id':prompt['node_id'],'review_status':'accepted_for_next_step','reviewed_sha256':'0'*64}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'stale_host_review'):
                prepare.reviewed_work(prompt,collection,reviewed,review)
            review.write_text(json.dumps({'task_id':'another-node','review_status':'accepted_for_next_step'}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'host_review_binding'):
                prepare.reviewed_work(prompt,collection,reviewed,review)

    def test_expected_answers_and_float_values_cannot_enter_public_missions(self):
        for value in ({'expected_answer':7},{'nested':{'oracle_answer':3}},{'weight':0.5}):
            with self.assertRaises(ValueError): prepare.public_exact(value)
        prepare.public_exact({'bound':'2','hypotheses':['one positive normalized joint law']})

    def test_fixed_answer_schemas_are_refused_but_exact_witness_shapes_are_allowed(self):
        for schema in ({'type':'integer','const':480},{'type':'boolean','enum':[True]},{'type':'number'},{'type':'integer','default':128}):
            with self.assertRaises(ValueError): prepare.witness_schema(schema)
        prepare.witness_schema({'type':'object','properties':{'numerator':{'type':'integer'},'denominator':{'type':'integer','minimum':1}}})

    def test_useful_math_values_remain_in_the_research_targets(self):
        index=json.loads((ROOT/'dag/operads/index.json').read_bytes())
        row=next(n for n in index['nodes'] if n['node_id']=='FQ-BELL-RATIONAL-VIOLATION-14-5')
        bell=ROOT/row['prompt']
        p=prepare.load(bell)
        self.assertEqual(p['node_id'],row['node_id'])
        self.assertIn('14/5',p['user_prompt'])
        self.assertNotIn('which equals',p['user_prompt'])

    def test_reviewed_next_step_can_be_prepared_without_self_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            reviewed,review=self.reviewed_fixture(directory)
            packet=prepare.build_packet(PROMPTS[0],'P1_DERIVE',attempt_id='candidate',reviewed_path=reviewed,review_path=review)
            self.assertEqual(packet['stage_id'],'P1_DERIVE')
            self.assertEqual(packet['dispatch_status'],'prepared_only_no_provider_or_checker_executed')

    def test_repair_uses_bounded_failure_classes_and_preserves_original_target(self):
        with tempfile.TemporaryDirectory() as directory:
            reviewed,review=self.reviewed_fixture(directory)
            candidate=Path(directory)/'candidate.json';candidate.write_text('0',encoding='utf-8')
            check=Path(directory)/'check.json'
            check.write_text(json.dumps({'task_id':prepare.load(PROMPTS[0])['node_id'],'candidate_sha256':prepare.digest(candidate.read_bytes()),'status':'repairable_candidate_defect','bounded_failure_codes':['G3_WITNESS'],'oracle_answer':'PRIVATE'}),encoding='utf-8')
            packet=prepare.build_packet(PROMPTS[0],'P3_REPAIR',attempt_id='repair',reviewed_path=reviewed,review_path=review,candidate_path=candidate,host_check_path=check)
            self.assertEqual(packet['public_context']['bounded_failure_codes'],['G3_WITNESS'])
            self.assertNotIn('PRIVATE',json.dumps(packet))
            self.assertNotIn('accepted_candidate',packet['public_context'])

    def test_challenge_requires_host_accepted_candidate_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            reviewed,review=self.reviewed_fixture(directory)
            candidate=Path(directory)/'candidate.json';candidate.write_text('0',encoding='utf-8')
            check=Path(directory)/'check.json'
            check.write_text(json.dumps({'task_id':prepare.load(PROMPTS[0])['node_id'],'candidate_sha256':'0'*64,'status':'accepted_candidate_for_challenge'}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'candidate_host_check_binding'):
                prepare.build_packet(PROMPTS[0],'P4_CHALLENGE',attempt_id='challenge',reviewed_path=reviewed,review_path=review,candidate_path=candidate,host_check_path=check)

    def test_bell_collected_compositions_are_typed_and_near_miss_is_refused(self):
        record=prepare.load(ROOT/'dag/operads/fq_bell_classical_joint_extension.yaml')
        presentation=record['presentation']
        self.assertEqual(audit.check_presentation(presentation),[])
        broken=copy.deepcopy(presentation)
        broken['generators'][0]['arity']=1
        self.assertIn('arity mismatch',audit.check_presentation(broken))
        broken=copy.deepcopy(presentation)
        broken['compositions'][0]['input_slot']=0
        self.assertIn('graft colour mismatch',audit.check_presentation(broken))


if __name__=='__main__': unittest.main()
