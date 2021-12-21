<template>
<div class="main" align="left">
	<div class="content">
		Preview Area
		<input type="color" style="float: right">
		<div style="float:right; padding:5px">Raster color:</div>
		<button style="float: right; margin-left: 10px;">Open Raster</button>
	</div>
	<div class="imgArea" @mousemove="getPos($event)" @click="sendCoord">
		<img :src="prev_img">
	</div>
	<div class="content">
		Cursor Position:
		<input type="number" v-model="mouse_r"> + <input type="number" v-model="mouse_i"> j
	</div>
	<div class="content">
		Current Center:
		<input type="number" :value="img_r"> + <input type="number" :value="img_i"> j
	</div>
	<div class="content">
		Current Radius:
		<input type="number" :value="radius">
	</div>
	<div>
	{{ show }}
	</div>
</div>
</template>



<script>
//:src="prev_img"
//"@/assets/empty.png"
export default {
	name: 'PreviewArea',
	props: {
		prev_img: String,
		img_r: Number,
		img_i: Number,
		radius: Number,
	},
	emits: ['sendCoord'],
	components:{
	},
	data () { return {
		variable: null,
		mouse_r: 0.0,
		mouse_i: 0.0,
		show: null,
	} },
	computed: {
		precision () { return 3-Math.log10(this.radius) },
	},
	methods: {
		getPos (e) {
			if (this.radius != null) {
				var rect = e.target.getBoundingClientRect();
				this.mouse_r = Number( (this.img_r + 
					this.radius*((e.clientX - rect.left)/rect.height*2-16/9))
					.toFixed(this.precision) );
				this.mouse_i = Number( (this.img_i -
					this.radius*((e.clientY - rect.top)/rect.height*2-1))
					.toFixed(this.precision) );
			}
		},
		sendCoord () {
			this.$emit('sendCoord', {
				mouse_r: this.mouse_r,
				mouse_i: this.mouse_i,
			} );
		},
	},
	mounted () {
	},
}
</script>



<style scoped>
/*.main>div {
	width: 100%;
	padding: 5px, 0px;
}*/
.main>div{
	max-width:100%;
	padding: 5px 0px;
}

img {
	width: 100%;
}
span {
	background: white;
}
input {
	border: hidden;
}
</style>
