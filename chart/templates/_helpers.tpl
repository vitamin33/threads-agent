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

{{/* Auto-render migrations Job, if on in stub-Postgres */}}
{{- define "threads.migrations" -}}
{{- if .Values.postgres.enabled }}
{{- include (print $.Template.BasePath "/templates/migrations-job.yaml") . }}
{{- end }}
{{- end }}

{{/* ------------------------------------------------------------------ */}}
{{/*  Database configuration helpers for consistency                    */}}
{{/* ------------------------------------------------------------------ */}}

{{/* Standard PostgreSQL DSN for all services */}}
{{- define "threads.postgres.dsn" -}}
{{- if .Values.postgres.enabled -}}
postgresql+psycopg2://{{ .Values.postgres.auth.username | default "postgres" }}:{{ .Values.postgres.auth.postgresPassword | default "pass" }}@postgres:5432/{{ .Values.postgres.auth.database | default "threads_agent" }}
{{- else -}}
postgresql+psycopg2://postgres:pass@postgres:5432/threads_agent
{{- end -}}
{{- end }}

{{/* Standard DATABASE_URL for services that use it */}}
{{- define "threads.database.url" -}}
{{- if .Values.postgres.enabled -}}
postgresql://{{ .Values.postgres.auth.username | default "postgres" }}:{{ .Values.postgres.auth.postgresPassword | default "pass" }}@postgres:5432/{{ .Values.postgres.auth.database | default "threads_agent" }}
{{- else -}}
postgresql://postgres:pass@postgres:5432/threads_agent
{{- end -}}
{{- end }}

{{/* Database credentials as separate values */}}
{{- define "threads.postgres.username" -}}
{{ .Values.postgres.auth.username | default "postgres" }}
{{- end }}

{{- define "threads.postgres.password" -}}
{{ .Values.postgres.auth.postgresPassword | default "pass" }}
{{- end }}

{{- define "threads.postgres.database" -}}
{{ .Values.postgres.auth.database | default "threads_agent" }}
{{- end }}
