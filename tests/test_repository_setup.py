"""Check publication safeguards without external dependencies."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class RepositorySetupTests(unittest.TestCase):
    def test_pages_artifact_and_deployment_require_explicit_main_opt_in(self):
        text=(ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
        guard="${{ vars.PAGES_DEPLOY_ENABLED == 'true' && github.ref == 'refs/heads/main' && github.event_name != 'pull_request' }}"
        quality,deploy=text.split('\n  deploy:',1)
        self.assertIn('if: '+guard,quality)
        self.assertIn('if: '+guard,deploy)
        self.assertIn('needs: quality',deploy)
        self.assertIn('path: dist/',quality)
        self.assertNotIn('pull_request_target:',text)
        self.assertIn('persist-credentials: false',quality)
        self.assertIn('permissions:\n  contents: read',text)
        self.assertNotIn('contents: write',text)

    @unittest.skipUnless(shutil.which('git'),'Git required for ignore rules')
    def test_private_exports_and_build_are_ignored_but_content_is_not(self):
        if not (ROOT/'.git').exists():self.skipTest('Requires checkout metadata')
        paths=['dist/index.html','original.xml','Lattes.zip','.env','.env.local','private/review.json','.venv/secret','test-results/report.json','credential.pem']
        result=subprocess.run(['git','check-ignore','--no-index','-z','--stdin'],cwd=ROOT,input='\0'.join(paths)+'\0',text=True,capture_output=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(set(filter(None,result.stdout.split("\0"))),set(paths))
        result=subprocess.run(['git','check-ignore','--no-index','content/publications.json'],cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(result.returncode,1,result.stderr)
