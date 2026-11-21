import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('site_cli',Path(__file__).parents[1]/'script.py')
cli=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

SOURCE="""<!DOCTYPE html><html><HEAD><style>#write {color:red}</style></HEAD><body><div id="write"><h1>进制与编码</h1><h2>二进制</h2><p>$a_i+b_j$</p><pre><code>if (a &lt; b) return 1;\n</code></pre></div></body></html>"""


class PolishTests(unittest.TestCase):
    def render(self,source):
        self.assertTrue(hasattr(cli,'render_polished_html'),'缺少可安全重复运行的注入函数')
        return cli.render_polished_html(source)

    def test_repeat_injection_preserves_typora_body_and_math(self):
        source=SOURCE.replace('</HEAD>',"<link href='./lecture-theme.css?v=old' rel='stylesheet'></HEAD>").replace('</body>',"<script defer src='./lecture-enhance.js'></script></body>")
        result=self.render(source)
        self.assertEqual(self.render(result),result)
        self.assertEqual(result.count('href="lecture-theme.css"'),1)
        self.assertEqual(result.count('src="lecture-enhance.js"'),1)
        self.assertIn('<style>#write {color:red}</style>',result)
        self.assertIn('<p>$a_i+b_j$</p><pre><code>if (a &lt; b) return 1;\n</code></pre>',result)

    def test_missing_document_boundaries_rejected(self):
        self.assertTrue(hasattr(cli,'render_polished_html'))
        with self.assertRaises(ValueError):cli.render_polished_html('<div id="write">正文</div>')

    def test_unrelated_styles_and_scripts_are_not_removed(self):
        source=SOURCE.replace('</HEAD>', '<link rel="stylesheet" href="my-lecture-theme.css"></HEAD>').replace('</body>', '<script src="my-lecture-enhance.js"></script></body>')
        enhanced=self.render(source)
        self.assertIn('href="my-lecture-theme.css"',enhanced)
        self.assertIn('src="my-lecture-enhance.js"',enhanced)

    def test_embedded_html_script_comments_and_srcdoc_are_untouched(self):
        demo='''<script>const demo = '<head></head><body>example</body>'; const tag='<link href="lecture-theme.css">';</script><!-- </head></body><script src="lecture-enhance.js"></script> --><iframe srcdoc="&lt;body&gt;example&lt;/body&gt;"></iframe>'''
        source=SOURCE.replace('</body>',demo+'</body>')
        enhanced=self.render(source)
        self.assertIn(demo,enhanced)
        self.assertTrue(enhanced.endswith('<script src="lecture-enhance.js"></script>\n</body></html>'))
        self.assertEqual(self.render(enhanced),enhanced)

    def test_dry_run_makes_no_file_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            page=folder/'Lec-topic.html';page.write_text(SOURCE,encoding='utf-8')
            with patch.object(cli,'MEMOS_DIR',folder):
                try:cli.polish_html('Lec-topic.html',dry_run=True)
                except TypeError:self.fail('polish 缺少只读预览能力')
            self.assertEqual(page.read_text(encoding='utf-8'),SOURCE)
            self.assertFalse((folder/'lecture-theme.css').exists())

    def test_all_includes_named_lectures_and_excludes_detail(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            for name in ['lec-001.html','Lec-array-basics.html','detail.html']:(folder/name).write_text(SOURCE,encoding='utf-8')
            with patch.object(cli,'MEMOS_DIR',folder):cli.polish_html('all')
            self.assertIn('lecture-enhance.js',(folder/'Lec-array-basics.html').read_text(encoding='utf-8'))
            self.assertNotIn('lecture-enhance.js',(folder/'detail.html').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
