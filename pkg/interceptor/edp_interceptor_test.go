package interceptor

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	triggersv1 "github.com/tektoncd/triggers/pkg/apis/triggers/v1beta1"
	"github.com/tektoncd/triggers/pkg/interceptors"
	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	codebaseApi "github.com/epam/edp-codebase-operator/v2/pkg/apis/edp/v1"
)

func TestEDPInterceptor_Process(t *testing.T) {
	scheme := runtime.NewScheme()
	utilruntime.Must(codebaseApi.AddToScheme(scheme))

	framework := "Java11"
	frameworkTransformed := "java11"
	codebase := &codebaseApi.Codebase{
		TypeMeta: metav1.TypeMeta{},
		ObjectMeta: metav1.ObjectMeta{
			Namespace: "test-ns",
			Name:      "demo",
		},
		Spec: codebaseApi.CodebaseSpec{
			Framework: &framework,
			BuildTool: "Maven",
		},
	}
	successExtensions := map[string]interface{}{
		"spec": codebaseApi.CodebaseSpec{
			Framework: &frameworkTransformed,
			BuildTool: "maven",
		},
	}
	triggersContext := &triggersv1.TriggerContext{
		TriggerID: "namespace/test-ns/triggers/name",
	}

	fakeClient := fake.NewClientBuilder().WithScheme(scheme).WithRuntimeObjects(codebase).Build()
	interceptor := NewEDPInterceptor(fakeClient, zap.NewNop().Sugar())

	tests := []struct {
		name    string
		request *triggersv1.InterceptorRequest
		want    *triggersv1.InterceptorResponse
	}{
		{
			name: "success gerrit payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"project": {"name": "demo"}}`,
				Context: triggersContext,
			},
			want: &triggersv1.InterceptorResponse{
				Extensions: successExtensions,
				Continue:   true,
			},
		},
		{
			name: "success github payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": {"name": "demo"}}`,
				Header:  map[string][]string{"X-GitHub-Event": {"data"}},
				Context: triggersContext,
			},
			want: &triggersv1.InterceptorResponse{
				Extensions: successExtensions,
				Continue:   true,
			},
		},
		{
			name: "success gitlab payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": {"name": "demo"}}`,
				Header:  map[string][]string{"X-Gitlab-Event": {"data"}},
				Context: triggersContext,
			},
			want: &triggersv1.InterceptorResponse{
				Extensions: successExtensions,
				Continue:   true,
			},
		},
		{
			name: "failed to unmarshal gerrit payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": `,
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "no project name in gerrit payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"project": {"field": "demo"}}`,
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "failed to unmarshal github payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": `,
				Header:  map[string][]string{"X-GitHub-Event": {"data"}},
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "no repository name in github payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": {"field": "demo"}}`,
				Header:  map[string][]string{"X-GitHub-Event": {"data"}},
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "failed to unmarshal gitlab payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": `,
				Header:  map[string][]string{"X-Gitlab-Event": {"data"}},
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "no repository name in gitlab payload",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"repository": {"field": "demo"}}`,
				Header:  map[string][]string{"X-Gitlab-Event": {"data"}},
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
		{
			name: "codebase not found",
			request: &triggersv1.InterceptorRequest{
				Body:    `{"project": {"name": "demo2"}}`,
				Context: triggersContext,
			},
			want: interceptors.Failf(codes.InvalidArgument, "error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := interceptor.Process(context.Background(), tt.request)

			// Disable checking equality of status message, equality of status code is enough.
			got.Status.Message = ""
			tt.want.Status.Message = ""

			assert.Equal(t, tt.want, got)
		})
	}
}

func TestEDPInterceptor_Execute(t *testing.T) {
	scheme := runtime.NewScheme()
	utilruntime.Must(codebaseApi.AddToScheme(scheme))

	framework := "Java11"
	frameworkTransformed := "java11"
	codebase := &codebaseApi.Codebase{
		TypeMeta: metav1.TypeMeta{},
		ObjectMeta: metav1.ObjectMeta{
			Namespace: "test-ns",
			Name:      "demo",
		},
		Spec: codebaseApi.CodebaseSpec{
			Framework: &framework,
			BuildTool: "Maven",
		},
	}
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).WithRuntimeObjects(codebase).Build()
	interceptor := NewEDPInterceptor(fakeClient, zap.NewNop().Sugar())

	tests := []struct {
		name     string
		reqBody  string
		wantResp *triggersv1.InterceptorResponse
		wantErr  assert.ErrorAssertionFunc
	}{
		{
			name:    "success",
			reqBody: `{"body": "{\"project\": {\"name\": \"demo\"}}", "context": {"trigger_id": "namespace/test-ns/triggers/name"}}`,
			wantResp: &triggersv1.InterceptorResponse{
				Extensions: map[string]interface{}{
					"spec": codebaseApi.CodebaseSpec{
						Framework: &frameworkTransformed,
						BuildTool: "maven",
					},
				},
				Continue: true,
			},
			wantErr: assert.NoError,
		},
		{
			name:    "failed to parse body",
			reqBody: `{"body": invalid data`,
			wantErr: assert.Error,
		},
		{
			name:    "failed to get codebase",
			reqBody: `{"body": "{\"project\": {\"name\": \"demo2\"}}", "context": {"trigger_id": "namespace/test-ns/triggers/name"}}`,
			wantResp: &triggersv1.InterceptorResponse{
				Continue: false,
				Status: triggersv1.Status{
					Code:    codes.InvalidArgument,
					Message: "failed to get codebase test-ns/demo2: codebases.v2.edp.epam.com \"demo2\" not found",
				},
			},
			wantErr: assert.NoError,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req, err := http.NewRequest(http.MethodPost, "https://www.tektoncd.com", strings.NewReader(tt.reqBody))
			require.NoError(t, err)

			got, err := interceptor.Execute(req)
			if !tt.wantErr(t, err) {
				return
			}

			if tt.wantResp != nil {
				want, err := json.Marshal(tt.wantResp)
				require.NoError(t, err)

				assert.JSONEq(t, string(want), string(got))
			}
		})
	}
}
