import importlib.util
import sys
sys.dont_write_bytecode = True
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('update',Path(__file__).parents[1]/'scripts/update.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class Conversion(unittest.TestCase):
    def test_semantics(self):
        data={'version':2,'rules':[{'domain':['api.example.com'],'domain_suffix':['example.org'],
              'domain_keyword':['openai'],'domain_regex':['^ai[0-9]+\\.example\\.com$'],
              'ip_cidr':['192.0.2.0/24','2001:db8::/32'],'process_name':['App.exe']}]}
        rules=u.convert(data)
        self.assertEqual(set(rules),{'DOMAIN,api.example.com','DOMAIN-SUFFIX,example.org',
            'DOMAIN-KEYWORD,openai','DOMAIN-REGEX,^ai[0-9]+\\.example\\.com$',
            'IP-CIDR,192.0.2.0/24,no-resolve','IP-CIDR6,2001:db8::/32,no-resolve'})
    def test_reject_unknown_and_invalid(self):
        for rule in [{'port':[443]},{'domain_suffix':['.example.com']},{'domain':['bad,REJECT']},
                     {'ip_cidr':['192.0.2.1/24']},{'domain_regex':['[']},{'domain_regex':['(?=a)a']},{'domain_regex':['a++']},{'domain':'example.com'}]:
            with self.subTest(rule=rule), self.assertRaises((ValueError,TypeError)):
                u.convert({'version':2,'rules':[rule]})
    def test_go_regex_rejection_keeps_output(self):
        for expression in [r'^example\.com\Z', 'a{1001}', '(a{100}){100}']:
            with self.subTest(expression=expression), tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'ai.yaml'; output.write_text('unchanged sentinel')
                source=Path(directory)/'source.json'
                import json
                source.write_text(json.dumps({'version':2,'rules':[{
                    'domain_suffix':[f'test{i}.example.com' for i in range(220)],
                    'domain_regex':[expression]}]}))
                with patch.object(sys,'argv',['update','--source-file',str(source),'--output',str(output)]):
                    with self.assertRaises(ValueError):u.main()
                self.assertEqual(output.read_text(),'unchanged sentinel')

    def test_guards(self):
        with self.assertRaises(ValueError):u.validate(list(map(str,range(199))))
        with self.assertRaises(ValueError):u.validate(list(map(str,range(239))),list(range(300)))
        u.validate(list(map(str,range(240))),list(range(300)))
        with self.assertRaises(ValueError):u.validate(['same']*200)

if __name__=='__main__':unittest.main()
