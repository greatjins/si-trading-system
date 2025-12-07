import { useEffect, useState } from 'react'
import { accountAPI } from '../../services/api'
import type { AccountInfo as AccountInfoType } from '../../types'

export function AccountInfo() {
  const [account, setAccount] = useState<AccountInfoType | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadAccount()
  }, [])
  
  const loadAccount = async () => {
    try {
      const data = await accountAPI.getAccount()
      setAccount(data)
    } catch (error) {
      console.error('Failed to load account:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) return <div>로딩 중...</div>
  if (!account) return <div>계좌 정보를 불러올 수 없습니다</div>
  
  const formatNumber = (num: number) => num.toLocaleString('ko-KR')
  
  return (
    <div style={styles.container}>
      <h3 style={styles.title}>계좌 정보</h3>
      <div style={styles.grid}>
        <div style={styles.item}>
          <div style={styles.label}>계좌번호</div>
          <div style={styles.value}>{account.account_id}</div>
        </div>
        <div style={styles.item}>
          <div style={styles.label}>예수금</div>
          <div style={styles.value}>{formatNumber(account.balance)}원</div>
        </div>
        <div style={styles.item}>
          <div style={styles.label}>평가금액</div>
          <div style={styles.value}>{formatNumber(account.equity)}원</div>
        </div>
        <div style={styles.item}>
          <div style={styles.label}>주문가능금액</div>
          <div style={styles.value}>{formatNumber(account.margin_available)}원</div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#2b2b2b',
    borderRadius: '8px',
    marginBottom: '20px',
  },
  title: {
    margin: '0 0 15px 0',
    color: '#d1d4dc',
    fontSize: '18px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '15px',
  },
  item: {
    padding: '10px',
    backgroundColor: '#1e1e1e',
    borderRadius: '4px',
  },
  label: {
    fontSize: '12px',
    color: '#888',
    marginBottom: '5px',
  },
  value: {
    fontSize: '16px',
    color: '#d1d4dc',
    fontWeight: 'bold',
  },
}
