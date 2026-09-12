{{/* Name helpers */}}
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "app.labels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/*
Selector labels. Immutable on a Deployment/Rollout, so a service migrating off an
older manifest can override these to MATCH its existing workload's selector
(e.g. {app: <name>}) → the flip becomes an in-place rolling update with no
delete/recreate and zero downtime. New services leave it unset (standard labels).
*/}}
{{- define "app.selectorLabels" -}}
{{- if .Values.selectorLabels -}}
{{ toYaml .Values.selectorLabels }}
{{- else -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- end -}}

{{/* pod spec shared by Deployment and Rollout */}}
{{- define "app.podSpec" -}}
{{- with .Values.imagePullSecrets }}
imagePullSecrets:
{{- range . }}
  {{- if kindIs "string" . }}
  - name: {{ . }}
  {{- else }}
  - {{ toYaml . | nindent 4 | trim }}
  {{- end }}
{{- end }}
{{- end }}
{{- if .Values.serviceAccount.create }}
serviceAccountName: {{ .Values.serviceAccount.name | default (include "app.fullname" .) }}
{{- else if .Values.serviceAccount.name }}
serviceAccountName: {{ .Values.serviceAccount.name }}
{{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automountServiceAccountToken }}
{{- with .Values.affinity }}
affinity:
{{ toYaml . | indent 2 }}
{{- end }}
{{- with .Values.nodeSelector }}
nodeSelector:
{{ toYaml . | indent 2 }}
{{- end }}
{{- with .Values.tolerations }}
tolerations:
{{ toYaml . | indent 2 }}
{{- end }}
{{- with .Values.topologySpreadConstraints }}
topologySpreadConstraints:
{{ toYaml . | indent 2 }}
{{- end }}
securityContext:
{{ toYaml .Values.podSecurityContext | indent 2 }}
containers:
  - name: {{ include "app.name" . }}
    image: "{{ required "image.repository is required" .Values.image.repository }}:{{ required "image.tag is required" .Values.image.tag }}"
    imagePullPolicy: {{ .Values.image.pullPolicy }}
    securityContext:
{{ toYaml .Values.securityContext | indent 6 }}
    ports:
{{- range .Values.ports }}
      - name: {{ .name }}
        containerPort: {{ .containerPort }}
        protocol: {{ .protocol | default "TCP" }}
{{- end }}
{{- with .Values.env }}
    env:
{{ toYaml . | indent 6 }}
{{- end }}
{{- with .Values.envFrom }}
    envFrom:
{{ toYaml . | indent 6 }}
{{- end }}
    resources:
{{ toYaml .Values.resources | indent 6 }}
{{- with .Values.startupProbe }}
    startupProbe:
{{ toYaml . | indent 6 }}
{{- end }}
{{- with .Values.livenessProbe }}
    livenessProbe:
{{ toYaml . | indent 6 }}
{{- end }}
{{- with .Values.readinessProbe }}
    readinessProbe:
{{ toYaml . | indent 6 }}
{{- end }}
{{- with .Values.writableDirs }}
    volumeMounts:
{{- range . }}
      - name: {{ .name }}
        mountPath: {{ .mountPath }}
{{- end }}
{{- end }}
{{- with .Values.writableDirs }}
volumes:
{{- range . }}
  - name: {{ .name }}
    emptyDir: {}
{{- end }}
{{- end }}
{{- end -}}
