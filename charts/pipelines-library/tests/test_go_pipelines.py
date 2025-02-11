import os
import sys

from .helpers import helm_template


def test_go_pipelines_gerrit():
    config = """
gerrit:
  enabled: true
    """

    r = helm_template(config)

    assert "gerrit-go-beego-app-review" in r["pipeline"]
    assert "gerrit-go-beego-app-build-default" in r["pipeline"]
    assert "gerrit-go-beego-app-build-edp" in r["pipeline"]

    # ensure pipelines have proper steps
    for buildtool in ['go']:
        for framework in ['beego']:

            gerrit_review_pipeline = f"gerrit-{buildtool}-{framework}-app-review"
            gerrit_build_pipeline_def = f"gerrit-{buildtool}-{framework}-app-build-default"
            gerrit_build_pipeline_edp = f"gerrit-{buildtool}-{framework}-app-build-edp"

            rt = r["pipeline"][gerrit_review_pipeline]["spec"]["tasks"]
            assert "fetch-repository" in rt[0]["name"]
            assert "gerrit-notify" in rt[1]["name"]
            assert "init-values" in rt[2]["name"]
            assert "build" in rt[3]["name"]
            assert "test" in rt[4]["name"]
            assert "fetch-target-branch" in rt[5]["name"]
            assert "sonar-prepare-files" in rt[6]["name"]
            assert "sonar-prepare-files-general" == rt[6]["taskRef"]["name"]
            assert "sonar" in rt[7]["name"]
            assert "dockerfile-lint" in rt[8]["name"]
            assert "dockerbuild-verify" in rt[9]["name"]
            assert "helm-lint" in rt[10]["name"]
            assert "gerrit-vote-success" in r["pipeline"][gerrit_review_pipeline]["spec"]["finally"][0]["name"]
            assert "gerrit-vote-failure" in r["pipeline"][gerrit_review_pipeline]["spec"]["finally"][1]["name"]

            # build with default versioning
            btd = r["pipeline"][gerrit_build_pipeline_def]["spec"]["tasks"]
            assert "fetch-repository" in btd[0]["name"]
            assert "gerrit-notify" in btd[1]["name"]
            assert "init-values" in btd[2]["name"]
            assert "get-version" in btd[3]["name"]
            # ensure we have default versioning
            assert f"get-version-{buildtool}-default" == btd[3]["taskRef"]["name"]
            assert "sonar-cleanup" in btd[4]["name"]
            assert "sast" in btd[5]["name"]
            assert "test" in btd[6]["name"]
            assert "golang-build" == btd[6]["taskRef"]["name"]
            assert "sonar" in btd[7]["name"]
            assert "sonarqube-scanner" == btd[7]["taskRef"]["name"]
            assert "build" in btd[8]["name"]
            assert "golang-build" == btd[8]["taskRef"]["name"]
            assert "create-ecr-repository" in btd[9]["name"]
            assert "kaniko-build" in btd[10]["name"]
            assert "git-tag" in btd[11]["name"]
            assert "update-cbis" in btd[12]["name"]

            # build with edp versioning
            btedp = r["pipeline"][gerrit_build_pipeline_edp]["spec"]["tasks"]
            assert "fetch-repository" in btedp[0]["name"]
            assert "gerrit-notify" in btedp[1]["name"]
            assert "init-values" in btedp[2]["name"]
            assert "get-version" in btedp[3]["name"]
            assert "get-version-edp" == btedp[3]["taskRef"]["name"]
            assert "sonar-cleanup" in btedp[4]["name"]
            assert "sast" in btedp[5]["name"]
            assert "test" in btedp[6]["name"]
            assert "golang-build" == btedp[6]["taskRef"]["name"]
            assert "sonar" in btedp[7]["name"]
            assert "sonarqube-scanner" == btedp[7]["taskRef"]["name"]
            assert "build" in btedp[8]["name"]
            assert "golang-build" == btedp[8]["taskRef"]["name"]
            assert "create-ecr-repository" in btd[9]["name"]
            assert "kaniko-build" in btedp[10]["name"]
            assert "git-tag" in btedp[11]["name"]
            assert "update-cbis" in btedp[12]["name"]

def test_go_pipelines_github():
    config = """
github:
  enabled: true
    """

    r = helm_template(config)
    vcs = "github"

    # ensure pipelines have proper steps
    for buildtool in ['go']:
        for framework in ['beego']:

            github_review_pipeline = f"{vcs}-{buildtool}-{framework}-app-review"
            github_build_pipeline_def = f"{vcs}-{buildtool}-{framework}-app-build-default"
            github_build_pipeline_edp = f"{vcs}-{buildtool}-{framework}-app-build-edp"

            assert github_review_pipeline in r["pipeline"]
            assert github_build_pipeline_def in r["pipeline"]
            assert github_build_pipeline_edp in r["pipeline"]

            rt = r["pipeline"][github_review_pipeline]["spec"]["tasks"]
            assert "github-set-pending-status" in rt[0]["name"]
            assert "fetch-repository" in rt[1]["name"]
            assert "init-values" in rt[2]["name"]
            assert "build" in rt[3]["name"]
            assert "test" in rt[4]["name"]
            assert "sonar" in rt[5]["name"]
            assert "dockerfile-lint" in rt[6]["name"]
            assert "dockerbuild-verify" in rt[7]["name"]
            assert "helm-lint" in rt[8]["name"]
            assert "github-set-success-status" in r["pipeline"][github_review_pipeline]["spec"]["finally"][0]["name"]
            assert "github-set-failure-status" in r["pipeline"][github_review_pipeline]["spec"]["finally"][1]["name"]

            # build with default versioning
            btd = r["pipeline"][github_build_pipeline_def]["spec"]["tasks"]
            assert "fetch-repository" in btd[0]["name"]
            assert "init-values" in btd[1]["name"]
            assert "get-version" in btd[2]["name"]
            # ensure we have default versioning
            assert f"get-version-{buildtool}-default" == btd[2]["taskRef"]["name"]
            assert "sast" in btd[3]["name"]
            assert "test" in btd[4]["name"]
            assert "golang-build" == btd[4]["taskRef"]["name"]
            assert "sonar" in btd[5]["name"]
            assert "sonarqube-scanner" == btd[5]["taskRef"]["name"]
            assert "build" in btd[6]["name"]
            assert "golang-build" == btd[6]["taskRef"]["name"]
            assert "create-ecr-repository" in btd[7]["name"]
            assert "kaniko-build" in btd[8]["name"]
            assert "git-tag" in btd[9]["name"]
            assert "update-cbis" in btd[10]["name"]

            # build with edp versioning
            btedp = r["pipeline"][github_build_pipeline_edp]["spec"]["tasks"]
            assert "fetch-repository" in btedp[0]["name"]
            assert "init-values" in btedp[1]["name"]
            assert "get-version" in btedp[2]["name"]
            assert "get-version-edp" == btedp[2]["taskRef"]["name"]
            assert "sast" in btedp[3]["name"]
            assert "test" in btedp[4]["name"]
            assert "golang-build" == btedp[4]["taskRef"]["name"]
            assert "sonar" in btedp[5]["name"]
            assert "sonarqube-scanner" == btedp[5]["taskRef"]["name"]
            assert "build" in btedp[6]["name"]
            assert "golang-build" == btedp[6]["taskRef"]["name"]
            assert "create-ecr-repository" in btd[7]["name"]
            assert "kaniko-build" in btedp[8]["name"]
            assert "git-tag" in btedp[9]["name"]
            assert "update-cbis" in btedp[10]["name"]
