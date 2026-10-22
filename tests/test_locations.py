import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1] / 'scripts/sync_emails.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class LocationTests(unittest.TestCase):
    def test_separates_workplace_from_school_and_headquarters(self):
        cases = [
            ('嵌入式实习生', '工作地点：南京市江北新区星火路20号', '南信大周边_企业实习线索'),
            ('南信大学生申请嵌入式实习', '工作地点：南京江宁区', '江苏_南京_其他区域或地址待核'),
            ('国电南自南京嵌入式', '总部地址：江北新区星火路8号；岗位仅标注南京', '江苏_南京_其他区域或地址待核'),
            ('南京嵌入式实习', '工作地点：江北新区团结路99号孵鹰大厦', '江北扩展区_通勤待核'),
            ('苏州电气实习', '南京信息工程大学学生；工作地点：苏州', '江苏_苏州_无锡_常州等'),
            ('南信大自动化本科生求教', '请教进组做电机项目', '南信大校内_科研实训'),
            ('长三角高新企业晨报｜南京苏州实习', '工作地点：南京星火路20号；苏州其他岗位', '其他或待确认地点'),
        ]
        for subject, body, expected in cases:
            with self.subTest(subject=subject):
                self.assertEqual(sync.classify_email(subject, '', body)['location_slug'], expected)

    def test_existing_records_are_reclassified_when_rebuilding(self):
        item = dict(id='sample', date='2026-10-22', subject='南京嵌入式实习', sender='', body='工作地点：江北新区星火路20号', summary='', **sync.classify_email('南京嵌入式实习', '', ''))
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            original = sync.EMAILS_DIR, sync.ARCHIVE_DIR
            sync.EMAILS_DIR = Path(directory)
            sync.ARCHIVE_DIR = Path(directory) / 'archive'
            try:
                sync.build_markdown_views([item])
                nearby = (Path(directory) / 'by_location/南信大周边_企业实习线索.md').read_text(encoding='utf-8')
                other = (Path(directory) / 'by_location/江苏_南京_其他区域或地址待核.md').read_text(encoding='utf-8')
                self.assertIn('sample.md', nearby)
                self.assertNotIn('sample.md', other)
            finally:
                sync.EMAILS_DIR, sync.ARCHIVE_DIR = original


if __name__ == '__main__':
    unittest.main()
