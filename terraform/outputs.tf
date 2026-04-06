output "s3_bucket_name" {
  value = aws_s3_bucket.airspace.bucket
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}