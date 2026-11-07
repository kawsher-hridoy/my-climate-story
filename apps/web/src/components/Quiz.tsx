import { useEffect, useState } from "react";
import { ArrowRight, Check, RotateCcw, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Story } from "../lib/types";
import { getProgress, setProgress } from "../lib/offline";
import { number } from "../lib/format";
import { useLocale } from "./shared";

export default function Quiz({ story }: { story: Story }) {
  const { t } = useTranslation();
  const locale = useLocale();
  const key = `quiz-${story.place.id}-${story.release.content_version}`;
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [checked, setChecked] = useState(false);
  const [finished, setFinished] = useState(false);
  useEffect(() => {
    let mounted = true;
    void getProgress(key)
      .then((progress) => {
        if (!mounted || !progress) return;
        setIndex(Math.min(progress.questionIndex, story.quiz.length - 1));
        setAnswers(progress.answers);
        setFinished(progress.finished);
        if (progress.answers.length > progress.questionIndex) {
          setSelected(progress.answers[progress.questionIndex]);
          setChecked(true);
        }
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [key, story.quiz.length]);
  const question = story.quiz[index];
  const score = answers.filter(
    (answer, i) => answer === story.quiz[i]?.correct_index,
  ).length;
  async function check() {
    if (selected === null) return;
    const next = [...answers];
    next[index] = selected;
    setAnswers(next);
    setChecked(true);
    await setProgress(key, {
      answers: next,
      questionIndex: index,
      finished: false,
    }).catch(() => undefined);
  }
  async function next() {
    if (index === story.quiz.length - 1) {
      setFinished(true);
      await setProgress(key, {
        answers,
        questionIndex: index,
        finished: true,
      }).catch(() => undefined);
    } else {
      setIndex(index + 1);
      setSelected(null);
      setChecked(false);
      await setProgress(key, {
        answers,
        questionIndex: index + 1,
        finished: false,
      }).catch(() => undefined);
    }
  }
  async function reset() {
    setIndex(0);
    setSelected(null);
    setAnswers([]);
    setChecked(false);
    setFinished(false);
    await setProgress(key, {
      answers: [],
      questionIndex: 0,
      finished: false,
    }).catch(() => undefined);
  }
  if (finished)
    return (
      <div className="quiz-finish">
        <span>
          <Sparkles size={34} />
        </span>
        <h3>{t("quizComplete")}</h3>
        <p>
          {t("quizScore")} <strong>{number(score, locale)}</strong>{" "}
          {t("quizOutOf")}
        </p>
        <button className="button secondary" onClick={() => void reset()}>
          <RotateCcw size={16} />
          {t("playAgain")}
        </button>
      </div>
    );
  return (
    <div className="quiz-card">
      <div className="quiz-progress">
        <span>
          {t("question")} {number(index + 1, locale)} /{" "}
          {number(story.quiz.length, locale)}
        </span>
        <div>
          {story.quiz.map((_, i) => (
            <span key={i} className={i <= index ? "filled" : ""} />
          ))}
        </div>
      </div>
      <fieldset disabled={checked}>
        <legend>{question.question[locale]}</legend>
        <div
          className={`quiz-options ${question.image_question ? "image-quiz-options" : ""}`}
        >
          {question.options.map((option, i) => {
            const image = question.image_question
              ? i === question.correct_index
                ? story.imagery.before
                : story.imagery.after
              : null;
            return (
              <label
                key={i}
                className={`quiz-option ${selected === i ? "selected" : ""} ${checked && i === question.correct_index ? "right-answer" : ""}`}
              >
                <input
                  type="radio"
                  name={`quiz-${key}-${index}`}
                  value={i}
                  checked={selected === i}
                  onChange={() => setSelected(i)}
                />
                {image && (
                  <img
                    src={image.url}
                    alt={`${option[locale]} · ${locale === "bn" ? "ভূদৃশ্যের ছবি" : "Landscape image"}`}
                    loading="lazy"
                  />
                )}
                <span>
                  <span className="option-letter">{["A", "B", "C"][i]}</span>
                  {option[locale]}
                </span>
                {checked && i === question.correct_index && <Check size={18} />}
              </label>
            );
          })}
        </div>
      </fieldset>
      {checked && (
        <div
          className={`quiz-feedback ${selected === question.correct_index ? "is-correct" : ""}`}
          role="status"
        >
          <strong>
            {selected === question.correct_index
              ? t("correct")
              : t("incorrect")}
          </strong>
          <p>{question.explanation[locale]}</p>
          <a href={question.source_url} target="_blank" rel="noreferrer">
            {t("readSource")}
          </a>
        </div>
      )}
      <div className="quiz-bottom">
        <span>{locale === "bn" ? "কৌতূহলী থাকো।" : "Stay curious."}</span>
        {checked ? (
          <button className="button primary" onClick={() => void next()}>
            {t("nextQuestion")}
            <ArrowRight size={16} />
          </button>
        ) : (
          <button
            className="button primary"
            disabled={selected === null}
            onClick={() => void check()}
          >
            {t("checkAnswer")}
            <ArrowRight size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
