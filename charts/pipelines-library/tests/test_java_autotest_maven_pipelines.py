import os
import sys

from .helpers import helm_template


def test_java_pipelines_gerrit():
    config = """
gerrit:
  enabled: true
    """

    r = helm_template(config)

    # ensure pipelines have proper steps
    for buildtool in ['maven']:
        for framework in ['java11', 'java8']:
            for cbtype in ['aut']:

                assert f"gerrit-{buildtool}-{framework}-{cbtype}-review" in r["pipeline"]
                assert f"gerrit-{buildtool}-{framework}-{cbtype}-build-default" in r["pipeline"]
                assert f"gerrit-{buildtool}-{framework}-{cbtype}-build-edp" in r["pipeline"]

                gerrit_review_pipeline = f"gerrit-{buildtool}-{framework}-{cbtype}-review"
                gerrit_build_pipeline_def = f"gerrit-{buildtool}-{framework}-{cbtype}-build-default"
                gerrit_build_pipeline_edp = f"gerrit-{buildtool}-{framework}-{cbtype}-build-edp"

                rt = r["pipeline"][gerrit_review_pipeline]["spec"]["tasks"]
                assert "fetch-repository" in rt[0]["name"]
                assert "gerrit-notify" in rt[1]["name"]
                assert "init-values" in rt[2]["name"]
                assert "test" in rt[3]["name"]
                assert "run-tests-for-autotests" == rt[3]["taskRef"]["name"]
                assert "fetch-target-branch" in rt[4]["name"]
                assert "sonar-prepare-files" in rt[5]["name"]
                assert f"sonar-prepare-files-{buildtool}" == rt[5]["taskRef"]["name"]
                assert "sonar" in rt[6]["name"]
                assert f"{buildtool}" == rt[6]["taskRef"]["name"]
                assert "gerrit-vote-success" in r["pipeline"][gerrit_review_pipeline]["spec"]["finally"][0]["name"]
                assert "gerrit-vote-failure" in r["pipeline"][gerrit_review_pipeline]["spec"]["finally"][1]["name"]

                # build with default versioning
                btd = r["pipeline"][gerrit_build_pipeline_def]["spec"]["tasks"]
                assert "fetch-repository" in btd[0]["name"]
                assert "gerrit-notify" in btd[1]["name"]
                assert "init-values" in btd[2]["name"]
                assert "sonar-cleanup" in btd[3]["name"]
                assert "get-version" in btd[4]["name"]
                assert "git-tag" in btd[5]["name"]

                # build with edp versioning
                btedp = r["pipeline"][gerrit_build_pipeline_edp]["spec"]["tasks"]
                assert "fetch-repository" in btedp[0]["name"]
                assert "gerrit-notify" in btedp[1]["name"]
                assert "init-values" in btedp[2]["name"]
                assert "sonar-cleanup" in btedp[3]["name"]
                assert "get-version" in btedp[4]["name"]
                assert "get-version-edp" == btedp[4]["taskRef"]["name"]
                assert "git-tag" in btedp[5]["name"]
