terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
    telegram = {
      source = "yi-jiayu/telegram"
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

provider "telegram" {
  bot_token = var.tg_bot_key
}

variable "cloud_id" {
  type        = string
  description = "Cloud id"
}

variable "folder_id" {
  type        = string
  description = "Folder id"
}

variable "tg_bot_key" {
  type        = string
  description = "Telegram bot key"
}

// Create service account
resource "yandex_iam_service_account" "sa-hw-1" {
  name        = "sa-hw-1"
  description = "service account for cheatsheet homework"
}

// Create archive zip with function code
resource "archive_file" "code_zip" {
  type        = "zip"
  output_path = "func.zip"
  source_dir  = "src"
}

// Create cloud function
resource "yandex_function" "cheatsheet-func" {
  name               = "cheatsheet-func"
  description        = "function for cheatsheet homework"
  user_hash          = archive_file.code_zip.output_sha256
  runtime            = "python37"
  entrypoint         = "main.handler"
  memory             = "128"
  service_account_id = yandex_iam_service_account.sa-hw-1.id
  execution_timeout  = "15"
  environment = {
    "TELEGRAM_BOT_TOKEN" = var.tg_bot_key,
    "FOLDER_ID"          = var.folder_id,
    "SA_API_KEY"         = yandex_iam_service_account_api_key.sa_api_key.secret_key
  }
  content {
    zip_filename = archive_file.code_zip.output_path
  }
  mounts {
    name = "mnt"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket.bucket
    }
  }
}

// Make function public
resource "yandex_function_iam_binding" "public-cheatsheet-func" {
  function_id = yandex_function.cheatsheet-func.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}

// Set telegram webhook
resource "telegram_bot_webhook" "webhook" {
  url = "https://api.telegram.org/bot${var.tg_bot_key}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.cheatsheet-func.id}"
}

// Grant permissions to modify bucket and objects
resource "yandex_resourcemanager_folder_iam_member" "sa-editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.sa-hw-1.id}"
}

// Grant permissions to use language models
resource "yandex_resourcemanager_folder_iam_member" "sa-gpt-user" {
  folder_id = var.folder_id
  role      = "ai.languageModels.user"
  member    = "serviceAccount:${yandex_iam_service_account.sa-hw-1.id}"
}

// Grant permissions to use OCR service
resource "yandex_resourcemanager_folder_iam_member" "sa-ocr-user" {
  folder_id = var.folder_id
  role      = "ai.vision.user"
  member    = "serviceAccount:${yandex_iam_service_account.sa-hw-1.id}"
}

// Create Static Access Keys
resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = yandex_iam_service_account.sa-hw-1.id
  description        = "static access key for object storage"
}

// Use keys to create bucket
resource "yandex_storage_bucket" "bucket" {
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
}

// Object for body of YandexGPT request
resource "yandex_storage_object" "object" {
  bucket = yandex_storage_bucket.bucket.id
  key    = "instruction_gpt.json"
  source = "gpt_body.json"
}

// Object for body of OCR request
resource "yandex_storage_object" "ocr_object" {
  bucket = yandex_storage_bucket.bucket.id
  key    = "ocr_body.json"
  source = "ocr_body.json"
}

// Service account API KEY for Yandex GPT
resource "yandex_iam_service_account_api_key" "sa_api_key" {
  service_account_id = yandex_iam_service_account.sa-hw-1.id
  description        = "service account api key for yandex gpt"
}
