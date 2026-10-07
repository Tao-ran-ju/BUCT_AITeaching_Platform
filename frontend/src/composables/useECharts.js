import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, shallowRef } from 'vue'

/**
 * 封装 ECharts 生命周期：init / setOption / resize / dispose。
 * 用法：const { setOption } = useECharts(elRef, initialOption)
 *       setOption({ ... })  // 后续更新
 */
export function useECharts(elRef, initialOption) {
  const chart = shallowRef(null)

  function setOption(option) {
    if (chart.value) {
      chart.value.setOption(option)
    }
  }

  function resize() {
    if (chart.value) {
      chart.value.resize()
    }
  }

  onMounted(() => {
    if (!elRef.value) return
    chart.value = echarts.init(elRef.value)
    if (initialOption) {
      chart.value.setOption(initialOption)
    }
    window.addEventListener('resize', resize)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    if (chart.value) {
      chart.value.dispose()
      chart.value = null
    }
  })

  return { chart, setOption, resize }
}
