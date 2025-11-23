<template>
  <v-card
    class="pa-6 elevation-10 dashboard-card"
    rounded="xl"
    :loading="!dashboardUrl"
  >
    <v-card-title class="text-h4 font-weight-bold mb-4">
       Financial Dashboard
    </v-card-title>

    <v-divider class="mb-6"></v-divider>

    <div v-if="dashboardUrl" class="dashboard-container">
      <iframe
        :src="dashboardUrl"
        width="100%"
        height="600"
        frameborder="0"
        allowfullscreen
        class="dashboard-iframe"
      ></iframe>
    </div>
    <v-skeleton-loader
      v-else
      class="mx-auto"
      max-width="100%"
      type="image"
      height="600"
    ></v-skeleton-loader>

    <v-card-actions v-if="dashboardUrl">
      <v-spacer></v-spacer>
      <span class="text-caption text-medium-emphasis">Data updated via AWS QuickSight.</span>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { lambda } from '../aws-config.js';

const dashboardUrl = ref('');

onMounted(async () => {
  try {
    const params = {
      FunctionName: 'getQuickSightDashboardUrl',
      InvocationType: 'RequestResponse',
    };
    const result = await lambda.invoke(params).promise();
    await new Promise(resolve => setTimeout(resolve, 500));

    const payload = JSON.parse(result.Payload);
    if (payload && payload.url) {
      dashboardUrl.value = payload.url;
    } else {
      console.error('URL was not found in Lambda payload.');
    }
  } catch (err) {
    console.error('Error loading dashboard URL:', err);
  }
});
</script>

<style scoped>
.dashboard-card {
   background-color: #f8f9fa;
   border-left: 5px solid #007bff;
}

.dashboard-iframe {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.dashboard-container {
  min-height: 600px;
}
</style>
