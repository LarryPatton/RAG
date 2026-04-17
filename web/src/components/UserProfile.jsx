export default function UserProfile({ profile }) {
  if (!profile) return null

  const tags = []
  if (profile.budget) tags.push({ label: `预算 ≤¥${profile.budget}`, color: 'bg-green-100 text-green-700' })
  if (profile.type) tags.push({ label: profile.type, color: 'bg-blue-100 text-blue-700' })
  if (profile.scenario) tags.push({ label: profile.scenario, color: 'bg-purple-100 text-purple-700' })
  if (profile.noise_cancellation) tags.push({ label: '需要降噪', color: 'bg-red-100 text-red-700' })
  if (profile.brand_preference) tags.push({ label: profile.brand_preference, color: 'bg-amber-100 text-amber-700' })

  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((tag, i) => (
        <span key={i} className={`text-xs px-2 py-0.5 rounded-full ${tag.color}`}>
          {tag.label}
        </span>
      ))}
    </div>
  )
}
