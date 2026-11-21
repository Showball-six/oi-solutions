import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('import_exams', Path(__file__).parents[1] / 'scripts/import_exams.py')
if spec and spec.loader and Path(spec.origin).exists():
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
else:
    module = None


class ImportTests(unittest.TestCase):
    def normalize(self, questions):
        self.assertIsNotNone(module, '题库导入模块尚未实现')
        return module.normalize_paper({'title': '测试卷', 'category': 'GESP', 'questions': questions}, 'test', 'abc')

    def test_objective_score_excludes_program_and_missing_answer(self):
        paper = self.normalize([
            {'id': 1, 'type': 'choice', 'score': 2, 'answer': 'A', 'options': [{'key': 'A', 'text': 'A'}]},
            {'id': 2, 'type': 'program', 'score': 25, 'answer': 'None'},
            {'id': 3, 'type': 'judge', 'score': 2, 'answer': ''},
        ])
        self.assertEqual(paper['objective_score'], 2)
        self.assertFalse(paper['questions'][2]['gradable'])

    def test_html_is_escaped_and_separate_code_preserved(self):
        paper = self.normalize([{'id': 1, 'type': 'judge', 'score': 2, 'answer': 'False', 'content': '<script>alert(1)</script>', 'code': 'int x = 1 < 2;'}])
        question = paper['questions'][0]
        self.assertNotIn('<script>', question['html'])
        self.assertIn('int x', question['html'])
        self.assertIn('&lt;', question['html'])

    def test_duplicate_display_ids_have_unique_internal_keys(self):
        paper = self.normalize([{'id': 1, 'type': 'judge', 'answer': True}, {'id': 1, 'type': 'judge', 'answer': False}])
        self.assertEqual([q['uid'] for q in paper['questions']], ['q1', 'q2'])
        self.assertEqual([q['answer'] for q in paper['questions']], ['True', 'False'])

    def test_multi_choice_requires_valid_options(self):
        paper = self.normalize([{'id': 1, 'type': 'multi_choice', 'answer': 'AC', 'options': [{'key': 'A', 'text': 'a'}, {'key': 'B', 'text': 'b'}]}])
        self.assertFalse(paper['questions'][0]['gradable'])

    def test_math_delimiters_preserve_tex_and_underscores(self):
        formula = r'$(926)_{{10}}=(1110011110)_{{2}}$'
        paper = self.normalize([{'id': 1, 'type': 'fill', 'answer': '1', 'content': formula}])
        self.assertIn(formula, paper['questions'][0]['html'])
        self.assertNotIn('<em>', paper['questions'][0]['html'])

    def test_unsafe_markdown_links_cannot_execute(self):
        paper = self.normalize([{'id': 1, 'type': 'fill', 'answer': '1', 'content': '[点此](javascript:alert(1))'}])
        self.assertNotIn('href="javascript:', paper['questions'][0]['html'])


if __name__ == '__main__':
    unittest.main()
