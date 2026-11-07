import {
  ArrowRight,
  ArrowUpRight,
  Globe2,
  Leaf,
  Printer,
  BookOpen,
  MapPin,
  Satellite,
  Thermometer,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eyebrow, useLocale } from "../components/shared";

export default function Info({
  kind,
}: {
  kind: "learn" | "teachers" | "sources" | "about" | "missing";
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const bn = locale === "bn";
  if (kind === "missing")
    return (
      <div className="section-width page-section">
        <h1>{t("notFound")}</h1>
        <Link className="button primary" to={`/${locale}/`}>
          {t("goHome")}
        </Link>
      </div>
    );
  const heading = {
    learn: ["learnEyebrow", "learnTitle"],
    teachers: ["teachersEyebrow", "teachersTitle"],
    sources: ["sourcesEyebrow", "sourcesTitle"],
    about: ["aboutEyebrow", "aboutTitle"],
  }[kind];
  return (
    <div
      className={`section-width page-section info-page ${kind === "teachers" ? "teacher-page" : ""}`}
    >
      <Eyebrow>{t(heading[0])}</Eyebrow>
      <h1 className="page-title">{t(heading[1])}</h1>
      {kind === "learn" && (
        <>
          <p className="page-intro">
            {bn
              ? "বড় ধারণা বোঝার শুরু ছোট প্রশ্নে। গল্পের চার্ট আর ছবি দেখার সময় এই শব্দগুলো কাজে লাগবে।"
              : "Big ideas start with small questions. These words help you read the images and charts in your story."}
          </p>
          <div className="glossary-grid">
            {[
              [
                bn ? "আবহাওয়া" : "Weather",
                bn
                  ? "একটি দিন বা স্বল্প সময়ে বাতাস, তাপমাত্রা, মেঘ আর বৃষ্টির অবস্থা।"
                  : "Conditions such as temperature, clouds, and rain over a short time.",
              ],
              [
                bn ? "জলবায়ু" : "Climate",
                bn
                  ? "বহু বছরের আবহাওয়ার ধরন। এক দিনের আবহাওয়া পুরো জলবায়ুর গল্প বলে না।"
                  : "Weather patterns across many years. One day does not tell the whole climate story.",
              ],
              [
                bn ? "গ্রিডের অনুমান" : "Gridded estimate",
                bn
                  ? "তথ্য একটি বড় অঞ্চলকে ঘরের মতো ভাগ করে বোঝায়। এটি প্রতিটি বাড়িতে মাপা তথ্য নয়।"
                  : "A dataset divides an area into cells. It does not measure every home independently.",
              ],
              [
                bn ? "গড়" : "Average",
                bn
                  ? "একই ধরনের মান যোগ করে মানের সংখ্যা দিয়ে ভাগ করা। মাসের দৈর্ঘ্য আলাদা হলে বার্ষিক তাপমাত্রায় দিনের ওজন ব্যবহার হয়।"
                  : "Values combined into a typical measure. Annual temperature accounts for different month lengths.",
              ],
              [
                bn ? "অ্যানোমালি" : "Anomaly",
                bn
                  ? "একটি ভিত্তিকালের গড় থেকে পার্থক্য। GISTEMP-এর ভিত্তিকাল ১৯৫১–১৯৮০।"
                  : "A difference from a reference average. The GISTEMP baseline is 1951–1980.",
              ],
              [
                bn ? "পর্যবেক্ষণ" : "Observation",
                bn
                  ? "ছবি বা তথ্যতে যা সত্যিই দেখা যায়। কারণ ব্যাখ্যা করতে আরও প্রমাণ দরকার।"
                  : "What the data or image actually shows. Explaining a cause requires more evidence.",
              ],
            ].map(([title, text], i) => (
              <div className="glossary-card" key={title}>
                <span>0{i + 1}</span>
                <h2>{title}</h2>
                <p>{text}</p>
              </div>
            ))}
          </div>
          <a
            className="button secondary"
            href="https://science.nasa.gov/kids/earth/"
            target="_blank"
            rel="noreferrer"
          >
            {bn ? "NASA-এর সঙ্গে আরও শেখো" : "Keep learning with NASA"}
            <ArrowUpRight size={17} />
          </a>
        </>
      )}
      {kind === "teachers" && (
        <>
          <p className="page-intro">
            {bn
              ? "৬–১০ শ্রেণির শিক্ষার্থীদের জন্য ৩৫ মিনিটের কাজ। একটি ইন্টারনেট সংযুক্ত বা সংরক্ষিত গল্পের ডিভাইস, কাগজ আর কৌতূহলই যথেষ্ট।"
              : "A 35-minute activity for grades 6–10. Bring one connected device or a saved story, paper, and curiosity."}
          </p>
          <button
            className="button secondary print-guide"
            onClick={() => window.print()}
          >
            <Printer size={17} />
            {bn ? "শিক্ষণ নির্দেশিকা প্রিন্ট" : "Print classroom guide"}
          </button>
          <div className="teacher-objectives">
            <BookOpen size={30} />
            <div>
              <h2>{bn ? "শেখার লক্ষ্য" : "Learning goals"}</h2>
              <p>
                {bn
                  ? "আবহাওয়া আর জলবায়ু আলাদা করা, ছবির উৎস আর তারিখ পড়া, চার্টের একক বোঝা, এবং পর্যবেক্ষণকে কারণের দাবি থেকে আলাদা করা।"
                  : "Distinguish weather and climate, read image dates and sources, interpret chart units, and separate observations from claims about cause."}
              </p>
            </div>
          </div>
          <div className="lesson-table">
            <table>
              <thead>
                <tr>
                  <th>{bn ? "সময়" : "Time"}</th>
                  <th>{bn ? "কাজ" : "Activity"}</th>
                  <th>{bn ? "আলোচনার প্রশ্ন" : "Discussion prompt"}</th>
                </tr>
              </thead>
              <tbody>
                {[
                  [
                    "5 min",
                    bn
                      ? "একটি পরিচিত জায়গা বেছে নাও"
                      : "Choose a familiar place",
                    bn
                      ? "এখানে কী কী দেখতে আশা করছ?"
                      : "What do you expect to see here?",
                  ],
                  [
                    "8 min",
                    bn ? "পুরোনো ও নতুন ছবি দেখো" : "Compare the images",
                    bn
                      ? "যা দেখছ আর তার ব্যাখ্যার মধ্যে পার্থক্য কী?"
                      : "How does an observation differ from an explanation?",
                  ],
                  [
                    "8 min",
                    bn
                      ? "তাপমাত্রা আর উৎস পড়ো"
                      : "Read temperature and sources",
                    bn
                      ? "তথ্যটি কত বড় এলাকা আর কোন সময় বোঝায়?"
                      : "What area and period does the dataset represent?",
                  ],
                  [
                    "7 min",
                    bn ? "কুইজ খেলে উত্তর আলোচনা" : "Play the quiz and discuss",
                    bn
                      ? "কোন উত্তরের জন্য আরও প্রমাণ চাই?"
                      : "Which answer would need more evidence?",
                  ],
                  [
                    "7 min",
                    bn
                      ? "একটি কাজ আর একটি প্রশ্ন লিখো"
                      : "Choose an action and write a question",
                    bn
                      ? "পরিবার বা ক্লাসের সঙ্গে কী করতে পারো?"
                      : "What can you try with your family or class?",
                  ],
                ].map((row) => (
                  <tr key={row[0] + row[1]}>
                    {row.map((cell, index) =>
                      index === 0 ? (
                        <th scope="row" key={index}>
                          {cell}
                        </th>
                      ) : (
                        <td key={index}>{cell}</td>
                      ),
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="worksheet">
            <h2>{bn ? "আমার গল্পের নোট" : "My story notes"}</h2>
            {[
              bn ? "আমার জায়গা ও ছবির তারিখ" : "My place and image dates",
              bn
                ? "আমি যে তিনটি বিষয় লক্ষ্য করেছি"
                : "Three things I observed",
              bn
                ? "তথ্যের উৎস, একক আর সময়কাল"
                : "The source, unit, and period",
              bn ? "আমার একটি প্রশ্ন" : "One question I still have",
              bn ? "আমাদের একটি নিরাপদ কাজ" : "One safe action we can try",
            ].map((text) => (
              <div key={text}>
                <strong>{text}</strong>
                <span />
              </div>
            ))}
          </div>
          <p className="quality-note">
            {bn
              ? "বৃষ্টির অধ্যায়ে তথ্য অপেক্ষায় থাকার কারণ নিয়েও কথা বলো। তথ্য না থাকা মানে শূন্য বৃষ্টি নয়। বাইরের কাজ বড়দের তত্ত্বাবধানে করো।"
              : "Discuss why the rainfall chapter is pending. Missing data does not mean zero rain. Outdoor activities need adult supervision."}
          </p>
        </>
      )}
      {kind === "sources" && (
        <>
          <p className="page-intro">
            {bn
              ? "প্রতিটি রেকর্ডের একটি উৎস, একক, সময়কাল আর সীমা আছে। নিচে মূল উৎসগুলো দেখো; গল্পের ভেতরে নির্দিষ্ট ছবির পরিচয় আর তথ্যের সংস্করণও দেওয়া আছে।"
              : "Every record has a source, unit, period, and limitations. These are the main sources; individual stories include scene identifiers and data release details."}
          </p>
          <div className="source-cards">
            {[
              {
                icon: Thermometer,
                name: "NASA POWER",
                tag: bn ? "আঞ্চলিক তাপমাত্রা" : "Regional temperature",
                text: bn
                  ? "১৯৮১–২০২৫ সালের মাসিক তথ্য; আঞ্চলিক গ্রিড প্রায় ০.৫° × ০.৬২৫°। মূল দৃশ্য ২০০১ থেকে, পুরোনো অংশের সীমা ব্যাখ্যাসহ।"
                  : "Monthly records from 1981–2025, around a 0.5° × 0.625° regional grid. The default view starts in 2001; older data has an explicit caveat.",
                url: "https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/",
              },
              {
                icon: Satellite,
                name: "USGS / NASA Landsat",
                tag: bn ? "ঐতিহাসিক ভূদৃশ্য" : "Historical landscapes",
                text: bn
                  ? "৩০ মিটার উৎসের রেজোলিউশন; সংগ্রহ করা, মেলানো আর যাচাই করা একই ঋতুর দৃশ্য। মূল উৎস USGS, ছবির হোস্ট Planetary Computer।"
                  : "30 m source pixels; retrieved, aligned, and reviewed similar-season scenes. USGS provenance with Planetary Computer hosting.",
                url: "https://www.usgs.gov/landsat-missions/spatiotemporal-asset-catalog-stac",
              },
              {
                icon: Globe2,
                name: "NASA GISTEMP v4",
                tag: bn ? "বিশ্বের প্রসঙ্গ" : "Global context",
                text: bn
                  ? "১৮৮০–২০২৫ সালের বৈশ্বিক স্থল–সমুদ্রের অ্যানোমালি। ১৯৫১–১৯৮০ গড়ের তুলনা; স্থানীয় তাপমাত্রা নয়।"
                  : "Global land–ocean anomalies, 1880–2025, relative to 1951–1980. This is separate from local absolute temperatures.",
                url: "https://data.giss.nasa.gov/gistemp/",
              },
              {
                icon: Leaf,
                name: "NASA IMERG Final V07B",
                tag: bn ? "বৃষ্টি · অপেক্ষায়" : "Rainfall · pending",
                text: bn
                  ? "নির্বাচিত বৃষ্টির উৎস, ০.১° গ্রিড। তথ্যের তালিকায় ১৯৯৮ থেকে ২০২৫-এর সেপ্টেম্বর; সর্বশেষ পুরো বছর ২০২৪। এই সংস্করণে মান এখনো সংগ্রহ হয়নি।"
                  : "Selected precipitation source at 0.1° resolution. Inspected catalog: 1998–September 2025, complete through 2024. Measurements are pending in this release.",
                url: "https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07",
              },
            ].map((source) => (
              <div className="source-card" key={source.name}>
                <source.icon size={25} />
                <span className="small-label">{source.tag}</span>
                <h2>{source.name}</h2>
                <p>{source.text}</p>
                <a
                  className="quiet-link"
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("readSource")}
                  <ArrowUpRight size={15} />
                </a>
              </div>
            ))}
          </div>
          <div className="additional-sources">
            <h2>
              {bn
                ? "মানচিত্র, নাম আর শিক্ষার উপকরণ"
                : "Maps, names, and learning resources"}
            </h2>
            <ul>
              <li>
                <a href="https://www.openstreetmap.org/copyright">
                  © OpenStreetMap contributors
                </a>{" "}
                — {bn ? "ইন্টারনেটে রাস্তার মানচিত্র" : "online street maps"}
              </li>
              <li>
                <a href="https://download.geonames.org/export/dump/readme.txt">
                  GeoNames · CC BY 4.0
                </a>{" "}
                —{" "}
                {bn ? "জায়গার নাম ও স্থানাঙ্ক" : "place names and coordinates"}
              </li>
              <li>
                <a href="https://www.naturalearthdata.com/about/terms-of-use/">
                  Natural Earth
                </a>{" "}
                — {bn ? "অফলাইনের সাধারণ মানচিত্র" : "offline overview map"}
              </li>
              <li>
                <a href="https://science.nasa.gov/kids/earth/">
                  NASA Earth education
                </a>
              </li>
              <li>
                <a href="https://www.unicef.org/bangladesh/en/press-releases/children-are-high-risk-amid-countrywide-heatwave-bangladesh">
                  UNICEF Bangladesh
                </a>{" "}
                —{" "}
                {bn
                  ? "শিশুদের গরমে নিরাপদ থাকার ধারণা"
                  : "child heat-safety guidance"}
              </li>
            </ul>
          </div>
        </>
      )}
      {kind === "about" && (
        <>
          <p className="page-intro">
            {bn
              ? "জলবায়ুর কথা অনেক সময় দূরের বিষয় মনে হয়। আমার জলবায়ুর গল্প শুরু হয় চেনা নদী, মাঠ আর শহর দিয়ে—তোমার আশপাশের পৃথিবী দিয়ে।"
              : "Climate can feel like a distant topic. My Climate Story starts with familiar rivers, fields, and towns—the world around you."}
          </p>
          <div className="about-story">
            <Leaf size={42} strokeWidth={1.2} />
            <h2>
              {bn
                ? "চেনা জায়গা, নতুন প্রশ্ন।"
                : "Familiar places. New questions."}
            </h2>
            <p>
              {bn
                ? "এটি NASA Space Apps-এর ধারণা থেকে তৈরি একটি স্বতন্ত্র শিক্ষামূলক প্রকল্প। NASA-এর উন্মুক্ত তথ্য ব্যবহার করে শিক্ষার্থীদের ছবি আর রেকর্ড পড়তে সাহায্য করে। যে তথ্য নেই বা যাচাই হয়নি, সেটিকে সেভাবেই দেখানো হয়।"
                : "This independent educational project grew from a NASA Space Apps concept. It uses open NASA data to help students read images and records, with clear labels where information is missing or unreviewed."}
            </p>
            <p>
              {bn
                ? "অ্যাকাউন্ট লাগে না। কুইজের ফল, কাজের তালিকা আর সংরক্ষিত গল্প এই ডিভাইসেই থাকে। মানচিত্রের নির্বাচিত বিন্দু অনুসন্ধানে সার্ভারে পাঠানো হয়; ডিভাইসের অবস্থানের অনুমতি শুধু তোমার অনুরোধে চাওয়া হয়।"
                : "No account is required. Quiz results, action choices, and saved packs stay on this device. Selected map coordinates are sent for data retrieval; device-location permission is requested only when you choose it."}
            </p>
            <Link className="button primary" to={`/${locale}/explore`}>
              <MapPin size={17} />
              {t("choosePlace")}
              <ArrowRight size={16} />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
