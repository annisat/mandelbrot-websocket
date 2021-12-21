<template>
  <MandelPanel/>
</template>

<script>
import MandelPanel from './components/MandelPanel.vue'

export default {
  name: 'App',
  components: {
    MandelPanel
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
