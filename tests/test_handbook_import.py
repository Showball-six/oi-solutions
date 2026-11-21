import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('unify_handbook',Path(__file__).parents[1]/'scripts/unify_handbook.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HandbookImportTests(unittest.TestCase):
    def test_new_export_replaces_old_chapter_order(self):
        self.assertTrue(hasattr(module,'read_books'),'更新导出时需要重新读取课程目录')
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)/'handbook'
            (base/'assets').mkdir(parents=True)
            (base/'courses/1').mkdir(parents=True)
            old=[{'id':1,'title':'旧名称','chapters':[{'path':'handbook/docs/old/index.html','title':'旧章节'}]}]
            (base/'assets/books.json').write_text(json.dumps(old),encoding='utf-8')
            (base/'courses/1/index.html').write_text('<h1>更新后的手册</h1><a href="../../docs/new/index.html"><span class="chapter-number">01</span><h2>新章节</h2></a><a href="../../docs/old/index.html"><span class="chapter-number">02</span><h2>旧章节</h2></a>',encoding='utf-8')
            books=module.read_books(base)
            self.assertEqual(books[0]['title'],'更新后的手册')
            self.assertEqual([c['title'] for c in books[0]['chapters']],['新章节','旧章节'])

    def test_unified_reader_reuses_manifest(self):
        self.assertTrue(hasattr(module,'read_books'))
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)/'handbook'
            (base/'assets').mkdir(parents=True)
            (base/'courses/1').mkdir(parents=True)
            old=[{'id':1,'title':'GESP 1级','chapters':[{'path':'handbook/docs/first/index.html','title':'第一章'}]}]
            (base/'assets/books.json').write_text(json.dumps(old),encoding='utf-8')
            (base/'courses/1/index.html').write_text('<article class="prose"><h1>第一章</h1></article>',encoding='utf-8')
            self.assertEqual(module.read_books(base),old)


if __name__=='__main__':unittest.main()
