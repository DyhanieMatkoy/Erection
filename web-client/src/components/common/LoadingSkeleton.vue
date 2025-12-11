<template>
  <div class="loading-skeleton" :class="skeletonClass">
    <!-- Table Skeleton -->
    <div v-if="type === 'table'" class="skeleton-table">
      <div class="skeleton-row skeleton-header">
        <div v-for="i in columns" :key="`header-${i}`" class="skeleton-cell"></div>
      </div>
      <div v-for="i in rows" :key="`row-${i}`" class="skeleton-row">
        <div v-for="j in columns" :key="`cell-${i}-${j}`" class="skeleton-cell"></div>
      </div>
    </div>

    <!-- Form Skeleton -->
    <div v-else-if="type === 'form'" class="skeleton-form">
      <div v-for="i in rows" :key="`field-${i}`" class="skeleton-field">
        <div class="skeleton-label"></div>
        <div class="skeleton-input"></div>
      </div>
    </div>

    <!-- Card Skeleton -->
    <div v-else-if="type === 'card'" class="skeleton-card">
      <div class="skeleton-card-header"></div>
      <div class="skeleton-card-body">
        <div v-for="i in rows" :key="`line-${i}`" class="skeleton-line"></div>
      </div>
    </div>

    <!-- List Skeleton -->
    <div v-else-if="type === 'list'" class="skeleton-list">
      <div v-for="i in rows" :key="`item-${i}`" class="skeleton-list-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-content">
          <div class="skeleton-title"></div>
          <div class="skeleton-subtitle"></div>
        </div>
      </div>
    </div>

    <!-- Text Skeleton (default) -->
    <div v-else class="skeleton-text">
      <div v-for="i in rows" :key="`text-${i}`" class="skeleton-line"></div>
    </div>
  </div>

</template>

<script setup lang="ts">
interface Props {
  type?: 'table' | 'form' | 'card' | 'list' | 'text'
  rows?: number
  columns?: number
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  rows: 3,
  columns: 4,
  animated: true
})

const skeletonClass = computed(() => ({
  'skeleton-animated': props.animated
}))
</script>

<script lang="ts">
import { computed } from 'vue'
export default {
  name: 'LoadingSkeleton'
}
</script>

<style scoped>
.loading-skeleton {
  width: 100%;
}

/* Animation */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton-animated .skeleton-cell,
.skeleton-animated .skeleton-label,
.skeleton-animated .skeleton-input,
.skeleton-animated .skeleton-line,
.skeleton-animated .skeleton-card-header,
.skeleton-animated .skeleton-title,
.skeleton-animated .skeleton-subtitle,
.skeleton-animated .skeleton-avatar {
  animation: shimmer 2s infinite linear;
  background: linear-gradient(
    to right,
    #f0f0f0 0%,
    #e0e0e0 20%,
    #f0f0f0 40%,
    #f0f0f0 100%
  );
  background-size: 2000px 100%;
}

/* Table Skeleton */
.skeleton-table {
  width: 100%;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  overflow: hidden;
}

.skeleton-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.skeleton-row:last-child {
  border-bottom: none;
}

.skeleton-header {
  background-color: #f8f9fa;
}

.skeleton-cell {
  flex: 1;
  height: 1.25rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

/* Form Skeleton */
.skeleton-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skeleton-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-label {
  width: 30%;
  height: 1rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

.skeleton-input {
  width: 100%;
  height: 2.5rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

/* Card Skeleton */
.skeleton-card {
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  overflow: hidden;
}

.skeleton-card-header {
  height: 3rem;
  background-color: #e9ecef;
  border-bottom: 1px solid #dee2e6;
}

.skeleton-card-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* List Skeleton */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-list-item {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.skeleton-avatar {
  width: 3rem;
  height: 3rem;
  background-color: #e9ecef;
  border-radius: 50%;
  flex-shrink: 0;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-title {
  width: 60%;
  height: 1rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

.skeleton-subtitle {
  width: 40%;
  height: 0.875rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

/* Text Skeleton */
.skeleton-text {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-line {
  height: 1rem;
  background-color: #e9ecef;
  border-radius: 0.25rem;
}

.skeleton-line:nth-child(odd) {
  width: 100%;
}

.skeleton-line:nth-child(even) {
  width: 85%;
}

.skeleton-line:last-child {
  width: 70%;
}
</style>
