<template>
  <v-container
    fluid
    class="d-flex justify-center align-center page-container"
  >
    <v-card
      class="pa-6 elevation-10 upload-card"
      rounded="xl"
      max-width="700"
    >
      <v-progress-linear
        v-if="isUploading"
        v-model="uploadProgress"
        color="success"
        height="10"
        striped
        absolute
      ></v-progress-linear>

      <v-card-title class="text-h4 font-weight-bold mb-4">
        Upload Financial Statement
      </v-card-title>

      <v-divider class="mb-6"></v-divider>

      <v-file-input
        v-model="file"
        label="Select your statement file (.csv or .xlsx)"
        accept=".csv,.xlsx"
        prepend-icon="mdi-file-upload-outline"
        variant="solo-filled"
        clearable
        :disabled="isUploading"
        color="primary"
        class="mb-6"
      />

      <v-btn
        color="success"
        size="large"
        @click="uploadFile"
        :disabled="!file || isUploading"
        :loading="isUploading"
        block
        class="font-weight-bold"
      >
        <v-icon start>mdi-cloud-upload</v-icon>
        {{ isUploading ? `${uploadProgress}%` : 'Upload' }}
      </v-btn>

      <v-btn
        color="primary"
        variant="outlined"
        size="large"
        to="/dashboard"
        block
        class="mt-4 font-weight-bold"
      >
        <v-icon start>mdi-view-dashboard</v-icon>
        Go to Dashboard
      </v-btn>
      <v-alert
        v-if="message"
        :type="alertType"
        :icon="alertIcon"
        class="mt-6"
        border="start"
        variant="tonal"
      >
        {{ message }}
      </v-alert>

    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Upload } from "@aws-sdk/lib-storage";
import { s3 } from '@/aws-config.js';

const file = ref(null);
const message = ref('');
const isUploading = ref(false);
const uploadSuccess = ref(null);
const uploadProgress = ref(0);

const alertType = computed(() => uploadSuccess.value ? 'success' : 'error');
const alertIcon = computed(() => uploadSuccess.value ? 'mdi-check-circle' : 'mdi-alert-circle');

const uploadFile = async () => {
  if (!file.value) return;

  message.value = '';
  uploadSuccess.value = null;
  isUploading.value = true;
  uploadProgress.value = 0;

  const params = {
    Bucket: 'pfa-demo-bucket2-sippel', // Remember to change this or use an env variable
    Key: file.value.name,
    Body: file.value,
    ContentType: file.value.type,
  };

  try {
    const upload = new Upload({
      client: s3,
      params: params,
      queueSize: 4,
      partSize: 1024 * 1024 * 5
    });

    upload.on("httpUploadProgress", (progress) => {
      if (progress.total) {
        uploadProgress.value = Math.round((progress.loaded / progress.total) * 100);
      }
    });

    await upload.done();

    uploadSuccess.value = true;
    message.value = `File "${file.value.name}" uploaded successfully!`;
    file.value = null;

  } catch (err) {
    console.error('Error uploading to S3 (SDK v3):', err);
    uploadSuccess.value = false;
    message.value = 'Error uploading the file. Check the console for details.';
  } finally {
    isUploading.value = false;
  }
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: white !important;
  padding: 30px;
}

.upload-card {
  width: 100%;
}
</style>
