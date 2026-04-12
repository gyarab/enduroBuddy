import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import WeekCardSkeleton from './WeekCardSkeleton.vue'

describe('WeekCardSkeleton', () => {
  const wrapper = mount(WeekCardSkeleton)

  it('renders root element', () => {
    expect(wrapper.find('.week-skeleton').exists()).toBe(true)
  })

  it('has header with title and stats bars', () => {
    const header = wrapper.find('.week-skeleton__header')
    expect(header.exists()).toBe(true)
    expect(header.find('.week-skeleton__bar--title').exists()).toBe(true)
    expect(header.find('.week-skeleton__bar--stats').exists()).toBe(true)
  })

  it('has exactly two columns', () => {
    const columns = wrapper.findAll('.week-skeleton__columns .week-skeleton__column')
    expect(columns).toHaveLength(2)
  })

  it('each column has a label', () => {
    const labels = wrapper.findAll('.week-skeleton__label')
    expect(labels).toHaveLength(2)
  })

  it('each column has 3 rows (6 total)', () => {
    const rows = wrapper.findAll('.week-skeleton__row')
    expect(rows).toHaveLength(6)
  })
})
