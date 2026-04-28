import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import KpiCard from '~/components/KpiCard.vue'

describe('KpiCard', () => {
  it('renders the label', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Total Production' }
    })
    expect(wrapper.text()).toContain('Total Production')
  })

  it('renders the value when provided', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Cost', value: '1,234 EUR' }
    })
    expect(wrapper.text()).toContain('1,234 EUR')
  })

  it('shows skeleton when loading', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Cost', loading: true }
    })
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
    // Value should not be rendered when loading
    expect(wrapper.findAll('p').some(p => p.classes().includes('text-3xl'))).toBe(false)
  })

  it('does not show skeleton when not loading', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Cost', value: '500 MW', loading: false }
    })
    expect(wrapper.find('.animate-pulse').exists()).toBe(false)
    expect(wrapper.text()).toContain('500 MW')
  })

  it('applies custom valueClass', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Status', value: 'OK', valueClass: 'text-green-400' }
    })
    const valueEl = wrapper.find('.text-3xl')
    expect(valueEl.classes()).toContain('text-green-400')
  })

  it('applies default text-white class when no valueClass', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Status', value: 'OK' }
    })
    const valueEl = wrapper.find('.text-3xl')
    expect(valueEl.classes()).toContain('text-white')
  })

  it('renders slot content', () => {
    const wrapper = mount(KpiCard, {
      props: { label: 'Progress', value: '75%' },
      slots: { default: '<div class="test-slot">Extra info</div>' }
    })
    expect(wrapper.find('.test-slot').exists()).toBe(true)
    expect(wrapper.text()).toContain('Extra info')
  })
})
