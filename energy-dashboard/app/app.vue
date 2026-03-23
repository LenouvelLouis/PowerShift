<template>
  <UApp>
    <NuxtLayout>
    </NuxtLayout>
  </UApp>
</template>

<script setup>
useHead({
  link: [{ rel: 'icon', href: '/favicon.ico' }],
  htmlAttrs: { lang: 'en' }
})

useSeoMeta({
  title: 'Energy Network Simulator 2026',
  description: 'Outil de simulation énergétique PyPSA',
})
</script>