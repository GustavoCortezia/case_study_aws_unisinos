<template>
  <v-card
    class="pa-6 elevation-10 dashboard-card"
    rounded="xl"
  >
    <div class="d-flex justify-space-between align-center mb-6">
      <v-card-title class="text-h4 font-weight-bold pl-0">
        Financial Dashboard
      </v-card-title>

      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-refresh"
        @click="fetchDataFromDatabase"
        :loading="isLoading"
      >
        Refresh Data
      </v-btn>
    </div>

    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="4">
        <v-card color="primary" class="pa-4 elevation-4" rounded="lg">
          <div class="d-flex flex-column text-white">
            <span class="text-caption text-uppercase mb-1 opacity-80 font-weight-bold">Total Expenses</span>
            <span class="text-h4 font-weight-bold">
              $ {{ isLoading ? '...' : totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
            </span>
          </div>
          <v-icon icon="mdi-cash-multiple" color="white" class="position-absolute" style="right: 16px; top: 16px; opacity: 0.2" size="64"></v-icon>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="4">
        <v-card color="surface-variant" variant="tonal" class="pa-4" rounded="lg">
          <div class="d-flex flex-column">
            <span class="text-caption text-uppercase mb-1 font-weight-bold">Transactions</span>
            <span class="text-h4 font-weight-bold">
              {{ isLoading ? '...' : rawTransactions.length }}
            </span>
          </div>
          <v-icon icon="mdi-receipt-text-outline" class="position-absolute" style="right: 16px; top: 16px; opacity: 0.2" size="64"></v-icon>
        </v-card>
      </v-col>
    </v-row>

    <v-divider class="mb-6"></v-divider>

    <div v-if="chartComponent && !isLoading && rawTransactions.length > 0" class="chart-container">
      <component
        :is="chartComponent"
        type="bar"
        height="350"
        :options="chartOptions"
        :series="series"
      />
    </div>

    <v-skeleton-loader
      v-else-if="isLoading"
      class="mx-auto"
      max-width="100%"
      type="image"
      height="350"
    ></v-skeleton-loader>

    <v-alert
      v-else-if="!isLoading && rawTransactions.length === 0"
      type="info"
      variant="tonal"
      class="mb-6"
    >
      No transactions found in the database.
    </v-alert>

    <v-alert
      v-else-if="errorMessage"
      type="error"
      variant="tonal"
      class="mb-6"
    >
      {{ errorMessage }}
    </v-alert>

    <v-expansion-panels class="mt-6">
      <v-expansion-panel title="View Detailed Data (Transactions Table)">
        <v-expansion-panel-text>
          <v-table density="compact">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th class="text-right">Amount ($)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in rawTransactions" :key="item.id">
                <td>{{ formatDate(item.date) }}</td>
                <td>
                  <v-chip size="x-small" label color="primary" variant="outlined">{{ item.category }}</v-chip>
                </td>
                <td>{{ item.description }}</td>
                <td class="text-right font-weight-bold" :class="item.amount < 0 ? 'text-red' : 'text-green'">
                  {{ item.amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

  </v-card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useTheme } from 'vuetify';
import { lambda } from '@/aws-config.js';
import { InvokeCommand } from "@aws-sdk/client-lambda";

const theme = useTheme();
const chartComponent = ref(null);
const isLoading = ref(false);
const rawTransactions = ref([]);
const errorMessage = ref('');

const totalBalance = computed(() => {
  return rawTransactions.value.reduce((acc, curr) => acc + Number(curr.amount), 0);
});

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return !isNaN(date) ? date.toLocaleDateString('en-US') : dateString;
};

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    toolbar: { show: false },
    fontFamily: 'Roboto, sans-serif'
  },
  plotOptions: {
    bar: {
      borderRadius: 6,
      horizontal: false,
      columnWidth: '45%',
      distributed: true
    }
  },
  dataLabels: { enabled: false },
  legend: { show: false },
  stroke: { show: true, width: 2, colors: ['transparent'] },
  xaxis: {
    categories: chartCategories.value,
    labels: {
      style: { fontSize: '12px', fontWeight: 500 }
    }
  },
  yaxis: {
    title: { text: 'Total ($)' }
  },
  grid: { borderColor: '#e0e0e0', strokeDashArray: 4 },
  colors: ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#546E7A', '#26a69a', '#D10CE8'],
  theme: {
    mode: theme.global.current.value.dark ? 'dark' : 'light'
  }
}));

const series = ref([{ name: 'Total', data: [] }]);
const chartCategories = ref([]);

const fetchDataFromDatabase = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    const command = new InvokeCommand({
      FunctionName: 'getUserTransactions',
      InvocationType: 'RequestResponse'
    });

    const response = await lambda.send(command);

    const payloadString = new TextDecoder("utf-8").decode(response.Payload);
    const payload = JSON.parse(payloadString);

    if (payload.errorMessage) {
      throw new Error(payload.errorMessage);
    }

    let transactionsData = [];

    if (Array.isArray(payload)) {
      transactionsData = payload;
    } else if (payload.body) {
      const bodyParsed = typeof payload.body === 'string' ? JSON.parse(payload.body) : payload.body;
      transactionsData = Array.isArray(bodyParsed) ? bodyParsed : [];
    }

    rawTransactions.value = transactionsData;
    processDataForChart(transactionsData);

  } catch (error) {
    console.error("Error fetching data from AWS:", error);
    errorMessage.value = "Failed to load data from AWS. Check console for details.";
    rawTransactions.value = [];
  } finally {
    isLoading.value = false;
  }
};

const processDataForChart = (transactions) => {
  const groupedData = {};

  transactions.forEach(t => {
    if (!groupedData[t.category]) {
      groupedData[t.category] = 0;
    }
    groupedData[t.category] += Number(t.amount);
  });

  chartCategories.value = Object.keys(groupedData);
  series.value = [{
    name: 'Expenses by Category',
    data: Object.values(groupedData).map(val => parseFloat(val.toFixed(2)))
  }];
};

onMounted(() => {
  import('vue3-apexcharts')
    .then((module) => {
      chartComponent.value = module.default;
      fetchDataFromDatabase();
    })
    .catch((err) => {
      console.error("Error loading ApexCharts:", err);
    });
});
</script>

<style scoped>
.dashboard-card {
  background-color: #f8f9fa;
}
.chart-container {
  min-height: 350px;
}
</style>
