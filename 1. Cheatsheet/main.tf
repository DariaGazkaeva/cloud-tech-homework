terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone                     = "ru-central1-d"
  service_account_key_file = pathexpand("~/.yc-keys/key.json")
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
}

variable "cloud_id" {
  type        = string
  description = "Cloud id"
}

variable "folder_id" {
  type        = string
  description = "Folder id"
}

resource "yandex_iam_service_account" "sa-hw-1" {
  name        = "sa-hw-1"
  description = "service account for cheatsheet homework"
}

resource "archive_file" "code_zip" {
  type        = "zip"
  output_path = "func.zip"
  source_dir  = "src"
}

resource "yandex_function" "cheatsheet-func" {
  name        = "cheatsheet-func"
  description = "function for cheatsheet homework"
  user_hash   = archive_file.code_zip.output_sha256
  runtime     = "python37"
  entrypoint  = "main.handler"
  memory      = "128"
  content {
    zip_filename = archive_file.code_zip.output_path
  }
}

resource "yandex_function_iam_binding" "public-cheatsheet-func" {
  function_id = yandex_function.cheatsheet-func.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}

output "cheatsheet-func-url" {
  value = "https://functions.yandexcloud.net/${yandex_function.cheatsheet-func.id}"
}
