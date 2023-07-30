<template>
<div class="panel" align="left">
	<div class="panel-content">
		Center = 
		<input type="number" placeholder='Real' v-bind="input_r">
		+
		<input type="number" placeholder='Imaginary' v-bind="input_i">
		j
	</div>
	<div class="panel-content">
		Radius = 
		<input type="number" placeholder='Radius' v-model="radius">
	</div>
	<div class="panel-content">
		Number of Iterations = 
		<input type="number" placeholder="Iterations" v-model="iterations">
	</div>
	<div class="panel-content">
		<button @click="startTask">Start</button>
		<button @click="pauseTask">{{ pauseButtonText }}</button>
		<button @click="stopTask">Stop</button>
	</div>
	<div class="panel-content">
		<progress max=100 :value="progress" :data-label="this.progress+'%'"></progress>
	</div>
</div>
</template>



<script>
export default {
	name: 'ParametersPanel',
	data () { return {
		radius: 1,
		iterations: 1000,
		pause_status: false,
	} },
	computed: {
		pauseButtonText () {
			return this.pause_status ? "Resume" : "Pause";
		},
	},
	props: {
		progress: Number,
		input_r: Number,
		input_i: Number,
	},
	emits: ['startTask', 'stopTask', 'pauseTask'],
	methods: {
		startTask () {
			this.$emit('startTask', {
				center_r: this.input_r,
				center_i: this.input_i,
				radius: this.radius,
				iterations: this.iterations
			} );
		},
		stopTask () {
			this.$emit('stopTask');
		},
		pauseTask () {
			this.pause_status = !this.pause_status;
			this.$emit('pauseTask', this.pause_status);
		},
	},
}
</script>



<style scoped>
.panel {
	border: gray solid 1px;
	clear: left;
	padding: 5px;
}
.panel-content {
	padding: 5px 0px;
}
input {
	border: hidden;
	width: 25%;
}
button {
	display: inline-block;
	margin-right: 20px;
}
progress {
	width: 100%;
	height: 20px;
}
</style>