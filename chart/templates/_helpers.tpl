{{/* ------------------------------------------------------------------ */}}
{{/*  Generic naming helpers – copied from `helm create`                */}}
{{/* ------------------------------------------------------------------ */}}

{{- define "threads.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "threads.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}

{{- define "threads.labels" -}}
app.kubernetes.io/name: {{ include "threads.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* ------------------------------------------------------------------ */}}
{{/*  NEW: image helper – required by orchestrator.yaml                 */}}
{{/* ------------------------------------------------------------------ */}}

{{- define "threads.image" -}}
{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}
