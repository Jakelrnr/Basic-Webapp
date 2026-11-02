type Props = React.InputHTMLAttributes<HTMLInputElement> & { label: string }

export function Input({ label, id, ...rest }: Props) {
  const inputId = id ?? rest.name
  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="text-sm text-zinc-400">{label}</label>
      <input
        id={inputId}
        {...rest}
        className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 focus:border-emerald-500 focus:outline-none"
      />
    </div>
  )
}