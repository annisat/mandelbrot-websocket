<template>
<div class="panel" align="left">
	<div class="coloringOptions">
		<label v-for="option in options" :key="option">
			<input type="radio" :value="option" name="colorOption" v-model="selectedColoring" @change="changeColor">
			<img :src="imgUrl(option)">
		</label>
	</div>
</div>
</template>



<script>
export default {
	name: 'ColoringPanel',
	data () { return {
		options: ['icy', 'flamboyant', 'flame'],
		selectedColoring: 'icy',
	} },
	emits: ['changeColor'],
	methods: {
		imgUrl: (fn) => { return require('@/assets/'+fn+'.png'); },
		changeColor () {
			this.$emit("changeColor", {coloring: this.selectedColoring} );
		},
	},
}
</script>



<style scoped>
.panel {
	border: gray solid 1px;
	clear: left;
	padding: 5px 0px;
}
.coloringOptions img {
	width: 90%;
	height: 20px;
	position: relative;
	top: 2px;
}
.coloringOptions input {
	width: 5%;
}
.coloringOptions label {
	display: block;
	margin: 10px 0px;
}
</style>