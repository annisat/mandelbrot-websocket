<template>
<div class="main-frame">
	<div class="grid control">
		<div class="tab" v-for="tab in tabs" :key=tab @click="currentTab = tab">
			{{ tab }}
		</div>
		<keep-alive><component
			class="panel"
			:is="currentTabComponent"
			@start-task="startTask($event)"
			@stop-task="stopTask"
			@pause-task="pauseTask"
			@change-color="changeColor"
			v-bind="{progress, input_r, input_i}"
		></component></keep-alive>
		<div class="msgbox">
		{{ return_data }}
		</div>
	</div>
	<PreviewArea class="grid preview" v-bind="{prev_img, img_r, img_i, radius}" @sendCoord="receiveCoord($event)"/>
</div>
</template>



<script>
import ParametersPanel from './ParametersPanel.vue'
import ColoringPanel from './ColoringPanel.vue'
import PreviewArea from './PreviewArea.vue'
import io from 'socket.io-client'

export default {
	name: 'MandelPanel',
	components: {
		ParametersPanel,
		ColoringPanel,
		PreviewArea,
	},
	data () { return {
		tabs: ['Parameters', 'Coloring'],
		currentTab: 'Parameters',
		socket: null,
		progress: 0.0,
		prev_img: require("@/assets/empty.png"),
		img_r: null,
		img_i: null,
		input_r: -0.5,
		input_i: 0,
		radius: null,
		return_data: null
	} },
	computed: {
		currentTabComponent () {
			return this.currentTab + 'Panel'
		},
	},
	methods: {
		startTask (data) {
			this.img_r = data.center_r;
			this.img_i = data.center_i;
			this.radius = data.radius;
			this.socket.emit('new_task', data);
		},
		stopTask () {
			this.socket.emit('stop');
		},
		pauseTask (pause_status) {
			if (pause_status) {
				this.socket.emit('pause');
			} else {
				this.socket.emit('resume');
			}
		},
		receiveCoord (data) {
			this.input_r = data.mouse_r;
			this.input_i = data.mouse_i;
		},
		changeColor (data) {
			this.socket.emit('changeColor', data);
		},
	},
	mounted () {
		this.socket = io.connect('http://localhost:5001');
		this.socket.on('update_draw', data => {
			this.prev_img = "data:image/png;base64," + data.img;
			this.progress = data.prog;
			console.log(this.progress);
		});
	},
}
</script>



<style scoped>
.main-frame {
	display: flex;
	background-color: gray;
	padding: 5px;
}
.grid {
	background-color: #bbffbb;
	margin: 5px;
	padding: 5px;
	align: left;
}
.control {
	width: 40vw;
}
.preview {
	width: 60vw;
}
.tab {
	border: gray solid 1px;
	padding: 5px;
	float: left;
	margin-right: -1px;
	margin-bottom: -1px;
	cursor: default;
}
.tab:hover {
	background: #99ee99;
}
.panel {
	max-width: 100%;
}
</style>
