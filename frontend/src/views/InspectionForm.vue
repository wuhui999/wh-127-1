<template>
  <div class="inspection-form-page">
    <el-page-header @back="$router.push('/inspections')" content="新建巡检" />

    <el-card shadow="hover" style="margin-top: 20px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 600px;">
        <el-form-item label="蜂箱" prop="hive_id">
          <el-select v-model="form.hive_id" placeholder="搜索选择蜂箱" filterable remote :remote-method="searchHives" :loading="hiveSearching" style="width: 100%">
            <el-option v-for="h in hiveOptions" :key="h.id" :label="`${h.hive_no} - ${h.status}`" :value="h.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="蜂群强度" prop="colony_strength">
          <el-slider v-model="form.colony_strength" :min="1" :max="10" :marks="strengthMarks" :style="{ '--el-slider-main-bg-color': strengthSliderColor }" />
          <div class="strength-label">
            <el-tag :type="strengthColor(form.colony_strength)" size="small">
              {{ form.colony_strength <= 3 ? '弱' : form.colony_strength <= 6 ? '中' : '强' }} ({{ form.colony_strength }}/10)
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="病虫害发现">
          <el-switch v-model="form.pest_disease" active-text="有" inactive-text="无" />
        </el-form-item>
        <el-form-item v-if="form.pest_disease" label="病虫害详情" prop="pest_detail">
          <el-input v-model="form.pest_detail" type="textarea" :rows="3" placeholder="请描述病虫害情况" />
        </el-form-item>

        <el-form-item label="需要补饲">
          <el-switch v-model="form.supplementary_feeding" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item v-if="form.supplementary_feeding" label="补饲详情" prop="feeding_detail">
          <el-input v-model="form.feeding_detail" type="textarea" :rows="3" placeholder="请描述补饲情况" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remarks" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>

        <el-form-item label="照片上传">
          <el-upload
            v-model:file-list="fileList"
            action="#"
            :auto-upload="false"
            list-type="picture-card"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">提交巡检</el-button>
          <el-button @click="$router.push('/inspections')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { inspectionApi, hiveApi } from '../api'

const router = useRouter()
const formRef = ref(null)
const submitLoading = ref(false)
const hiveSearching = ref(false)
const hiveOptions = ref([])
const fileList = ref([])

const form = reactive({
  hive_id: null,
  colony_strength: 5,
  pest_disease: false,
  pest_detail: '',
  supplementary_feeding: false,
  feeding_detail: '',
  remarks: ''
})

const rules = {
  hive_id: [{ required: true, message: '请选择蜂箱', trigger: 'change' }],
  colony_strength: [{ required: true, message: '请设置蜂群强度', trigger: 'change' }],
  pest_detail: [{ required: true, message: '请描述病虫害情况', trigger: 'blur' }],
  feeding_detail: [{ required: true, message: '请描述补饲情况', trigger: 'blur' }]
}

const strengthMarks = {
  1: '1',
  3: '3',
  5: '5',
  7: '7',
  10: '10'
}

const strengthSliderColor = computed(() => {
  if (form.colony_strength <= 3) return '#f56c6c'
  if (form.colony_strength <= 6) return '#e6a23c'
  return '#67c23a'
})

function strengthColor(val) {
  if (val <= 3) return 'danger'
  if (val <= 6) return 'warning'
  return 'success'
}

async function searchHives(query) {
  if (!query) return
  hiveSearching.value = true
  try {
    const { data } = await hiveApi.list({ keyword: query, size: 50 })
    hiveOptions.value = data.items || data || []
  } catch {
    hiveOptions.value = []
  } finally {
    hiveSearching.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    const payload = { ...form }
    payload.photo_names = fileList.value.map(f => f.name || f.url)
    await inspectionApi.create(payload)
    ElMessage.success('巡检提交成功')
    router.push('/inspections')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败')
  } finally {
    submitLoading.value = false
  }
}

searchHives('')
</script>

<style scoped>
.strength-label {
  margin-top: 8px;
}
</style>
