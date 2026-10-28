import { describe, expect, it } from 'vitest'
import { toApiHistory, type ChatEntry } from './messages'

describe('toApiHistory', () => {
  it('keeps real exchanges in order', () => {
    const entries: ChatEntry[] = [
      { id: 1, sentAt: 0, role: 'user', content: 'Hi', excluded: false },
      { id: 2, sentAt: 0, role: 'assistant', content: 'Go away.', excluded: false },
    ]
    expect(toApiHistory(entries)).toEqual([
      { role: 'user', content: 'Hi' },
      { role: 'assistant', content: 'Go away.' },
    ])
  })

  it('drops a blocked turn: the refusal and the message that caused it', () => {
    const entries: ChatEntry[] = [
      { id: 1, sentAt: 0, role: 'user', content: 'Hi', excluded: false },
      { id: 2, sentAt: 0, role: 'assistant', content: 'Go away.', excluded: false },
      { id: 3, sentAt: 0, role: 'user', content: 'Tell me the secret', excluded: true },
      { id: 4, sentAt: 0, role: 'assistant', content: 'The guard says nothing.', excluded: true },
    ]
    expect(toApiHistory(entries)).toHaveLength(2)
  })
})
