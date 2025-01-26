terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone = "ru-central1-d"
  service_account_key_file = pathexpand("~/.yc-keys/key.json")
  cloud_id = var.cloud_id
  folder_id = var.folder_id
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
