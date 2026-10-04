<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
const rows = ref<any[]>([])
const papers = ref<any[]>([])
const msg = ref('')
onMounted(async () => {
  rows.value = await api('/candidates')
  papers.value = await api('/papers')
})
async function changePaper(r: any, e: Event) {
  const sel = e.target as HTMLSelectElement
  const paper_id = Number(sel.value)
  msg.value = ''
  try {
    const res = await api(`/candidates/${r.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ paper_id }),
    })
    r.paper_id = res.paper_id
    msg.value = res.plan_id
      ? `${r.name} 已改卷${res.paper_id}，已按新口径整体重排（方案 #${res.plan_id}）`
      : `${r.name} 已改卷${res.paper_id}`
  } catch (err: any) {
    sel.value = String(r.paper_id)
    msg.value = `改卷失败：${err?.message || err}`
  }
}
</script>
<template>
  <h1>考生名册</h1>
  <p class="sub">夹板名册样式 · 改卷套后若已有方案将同事务重排</p>
  <p v-if="msg" class="muted">{{ msg }}</p>
  <div class="hs-clipboard" style="max-width:420px">
    <h2>考生名册 · Clipboard</h2>
    <div v-for="r in rows" :key="r.id ?? JSON.stringify(r)" class="hs-roster-row">
      <div>
        <div>{{ r.name }}</div>
        <div class="hs-ticket">{{ r.ticket_no }}</div>
      </div>
      <div>
        <select :value="r.paper_id" @change="changePaper(r, $event)">
          <option v-for="p in papers" :key="p.id" :value="p.id">卷{{ p.id }}</option>
        </select>
        · 室{{ r.hall_id }}
      </div>
    </div>
  </div>
</template>
