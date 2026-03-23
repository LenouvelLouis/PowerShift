export async function getDemandData() {
  try {
    const response = await $fetch('http://localhost:8000/api/v1/demands', {
      method: 'GET',
    })
    return response
  } catch (error) {
    console.error('Erreur de communication avec FastAPI:', error)
    return null
  }
}
