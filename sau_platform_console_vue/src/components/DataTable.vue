<template>
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? { width: col.width } : undefined"
            :class="{ sortable: col.sortable !== false }"
            @click="toggleSort(col)"
          >
            <span class="th-content">
              {{ col.label }}
              <span v-if="col.sortable !== false" class="sort-indicator">
                <span v-if="sortKey === col.key">{{ sortDirection === 'asc' ? '↑' : '↓' }}</span>
                <span v-else>↕</span>
              </span>
            </span>
          </th>
        </tr>
      </thead>
      <tbody v-if="pagedRows.length">
        <tr
          v-for="row in pagedRows"
          :key="rowKey(row)"
          :class="{ selected: selectedKey && rowKey(row) === selectedKey }"
          @click="$emit('select', row)"
        >
          <td v-for="col in columns" :key="col.key">
            <slot :name="`cell-${col.key}`" :row="row" :value="read(row, col.key)">
              {{ read(row, col.key) }}
            </slot>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td :colspan="columns.length" class="empty">{{ emptyText }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-if="showPagination && totalPages > 1" class="table-footer">
    <div class="stats-line">第 {{ currentPage }} / {{ totalPages }} 页，共 {{ sortedRows.length }} 条</div>
    <div class="toolbar">
      <select v-model.number="pageSize" style="width: 96px">
        <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}/页</option>
      </select>
      <button class="secondary" @click="goPrev" :disabled="currentPage <= 1">上一页</button>
      <button class="secondary" @click="goNext" :disabled="currentPage >= totalPages">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

export type DataTableColumn = {
  key: string;
  label: string;
  width?: string;
  sortable?: boolean;
};

const props = withDefaults(
  defineProps<{
    columns: DataTableColumn[];
    rows: Record<string, any>[];
    rowId?: string;
    selectedKey?: string;
    emptyText?: string;
    showPagination?: boolean;
    defaultPageSize?: number;
    pageSizeOptions?: number[];
  }>(),
  {
    rowId: "id",
    selectedKey: "",
    emptyText: "暂无数据",
    showPagination: true,
    defaultPageSize: 10,
    pageSizeOptions: () => [10, 20, 50],
  }
);

defineEmits<{
  (e: "select", row: Record<string, any>): void;
}>();

const currentPage = ref(1);
const pageSize = ref(props.defaultPageSize);
const sortKey = ref("");
const sortDirection = ref<"asc" | "desc">("asc");

const sortedRows = computed(() => {
  const items = [...props.rows];
  if (!sortKey.value) return items;
  return items.sort((a, b) => compareValues(read(a, sortKey.value), read(b, sortKey.value), sortDirection.value));
});

const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)));

const pagedRows = computed(() => {
  if (!props.showPagination) return sortedRows.value;
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedRows.value.slice(start, start + pageSize.value);
});

watch(
  () => props.rows,
  () => {
    if (currentPage.value > totalPages.value) currentPage.value = totalPages.value;
    if (currentPage.value < 1) currentPage.value = 1;
  },
  { deep: true }
);

watch(pageSize, () => {
  currentPage.value = 1;
});

watch(
  () => props.selectedKey,
  (key) => {
    if (!key || !props.showPagination) return;
    const index = sortedRows.value.findIndex((row) => rowKey(row) === key);
    if (index >= 0) currentPage.value = Math.floor(index / pageSize.value) + 1;
  },
  { immediate: true }
);

function read(row: Record<string, any>, key: string) {
  return row?.[key] ?? "";
}

function rowKey(row: Record<string, any>) {
  return String(row?.[props.rowId] ?? "");
}

function toggleSort(col: DataTableColumn) {
  if (col.sortable === false) return;
  if (sortKey.value !== col.key) {
    sortKey.value = col.key;
    sortDirection.value = "asc";
    currentPage.value = 1;
    return;
  }
  sortDirection.value = sortDirection.value === "asc" ? "desc" : "asc";
  currentPage.value = 1;
}

function goPrev() {
  if (currentPage.value > 1) currentPage.value -= 1;
}

function goNext() {
  if (currentPage.value < totalPages.value) currentPage.value += 1;
}

function compareValues(a: any, b: any, direction: "asc" | "desc") {
  const left = normalizeValue(a);
  const right = normalizeValue(b);
  if (left < right) return direction === "asc" ? -1 : 1;
  if (left > right) return direction === "asc" ? 1 : -1;
  return 0;
}

function normalizeValue(value: any) {
  if (value == null) return "";
  if (typeof value === "number") return value;
  const raw = Array.isArray(value) ? value.join(", ") : String(value);
  const asNumber = Number(raw);
  if (!Number.isNaN(asNumber) && raw.trim() !== "") return asNumber;
  const asDate = Date.parse(raw);
  if (!Number.isNaN(asDate) && /[-:TZ]/.test(raw)) return asDate;
  return raw.toLowerCase();
}
</script>
