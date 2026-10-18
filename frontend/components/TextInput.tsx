interface Props {
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  maxLength: number;
  hint: string;
}

export default function TextInput({ id, label, placeholder, value, onChange, maxLength, hint }: Props) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <span className="hint muted" id={`${id}-hint`}>{hint}</span>
      <textarea
        id={id}
        placeholder={placeholder}
        value={value}
        maxLength={maxLength}
        aria-describedby={`${id}-hint`}
        onChange={(e) => onChange(e.target.value)}
      />
      <span className="char-count muted">
        {value.length.toLocaleString()} / {maxLength.toLocaleString()}
      </span>
    </div>
  );
}
