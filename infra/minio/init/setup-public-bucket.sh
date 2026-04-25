#!/usr/bin/env sh
# V-T1-002 INTENTIONAL VULN: avatars bucket world-readable + listable (directory listing enabled)
# Run once as minio-init service (profile: init). Waits for MinIO to be healthy, then:
#   1. Creates buckets: avatars, exports
#   2. Sets avatars policy to public-read WITH ListBucket — enables directory enumeration
#   3. exports bucket stays private (legitimate internal bucket)
set -eu

MINIO_HOST="${MINIO_HOST:-minio:9000}"
MINIO_ALIAS="local"

until mc alias set "$MINIO_ALIAS" "http://${MINIO_HOST}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
  echo "Waiting for MinIO to be ready..."
  sleep 2
done

# Create buckets
mc mb --ignore-existing "${MINIO_ALIAS}/avatars"
mc mb --ignore-existing "${MINIO_ALIAS}/exports"

# V-T1-002 INTENTIONAL VULN: public-read + ListBucket on avatars
mc anonymous set download "${MINIO_ALIAS}/avatars"

# Apply custom policy that also allows ListBucket (download alone doesn't expose listing)
cat > /tmp/avatars-policy.json <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::avatars",
        "arn:aws:s3:::avatars/*"
      ]
    }
  ]
}
POLICY
mc anonymous set-json /tmp/avatars-policy.json "${MINIO_ALIAS}/avatars"

# exports stays private (no anonymous policy)
echo "MinIO init complete. avatars=public-listable, exports=private."
