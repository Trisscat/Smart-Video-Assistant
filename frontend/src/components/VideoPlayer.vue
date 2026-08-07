<template>
  <div class="video-player">
    <video
      ref="videoEl"
      :src="src"
      controls
      preload="metadata"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoaded"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true },
  seekTime: { type: Number, default: -1 },
})

const emit = defineEmits(['timeUpdate'])

const videoEl = ref(null)

watch(() => props.seekTime, (time) => {
  if (time >= 0 && videoEl.value) {
    videoEl.value.currentTime = time
    videoEl.value.play()
  }
})

function onTimeUpdate() {
  if (videoEl.value) emit('timeUpdate', videoEl.value.currentTime)
}

function onLoaded() {}

function seekTo(seconds) {
  if (videoEl.value) {
    videoEl.value.currentTime = seconds
    videoEl.value.play()
  }
}

defineExpose({ seekTo })
</script>

<style scoped>
.video-player {
  background: #000;
  border-radius: var(--radius);
  overflow: hidden;
}
video {
  width: 100%;
  display: block;
  border-radius: var(--radius);
}
</style>
