/**
 * Unit tests for time formatting in ComparePage
 * Tests the shortenTime helper function and fmtDuration function
 */

// Mock the time formatting functions from ComparePage
const fmtDuration = (secs) => {
  if (secs == null || isNaN(secs)) return null;
  const m = Math.round(secs / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  return r ? `${h} h ${r} min` : `${h} h`;
};

const shortenTime = (timeStr) => {
  if (!timeStr || timeStr === "--") return timeStr;
  // Replace "hour" or "hours" with " h", "hr" with " h", "mins" with "min"
  return timeStr
    .replace(/\s*hours?\s*/gi, " h ")
    .replace(/\s*hr\s*/gi, " h ")
    .replace(/\s*mins\s*/gi, " min ")
    .replace(/(\d)h\s*/gi, "$1 h ")  // Ensure space between digit and h
    .trim();
};

// Test cases
const testCases = [
  // fmtDuration tests
  { input: 300, expected: "5 min", func: "fmtDuration", description: "5 minutes" },
  { input: 60, expected: "1 min", func: "fmtDuration", description: "1 minute (no plural)" },
  { input: 3600, expected: "1 h", func: "fmtDuration", description: "1 hour exact" },
  { input: 4500, expected: "1 h 15 min", func: "fmtDuration", description: "1 hour 15 minutes" },
  { input: 7200, expected: "2 h", func: "fmtDuration", description: "2 hours exact" },
  { input: 9000, expected: "2 h 30 min", func: "fmtDuration", description: "2 hours 30 minutes" },
  { input: 45, expected: "1 min", func: "fmtDuration", description: "45 seconds rounds to 1 min" },
  { input: 90, expected: "2 min", func: "fmtDuration", description: "90 seconds rounds to 2 min" },
  
  // shortenTime tests (Google API format conversions)
  { input: "25 mins", expected: "25 min", func: "shortenTime", description: "mins to min" },
  { input: "1 hour 15 mins", expected: "1 h 15 min", func: "shortenTime", description: "hour + mins" },
  { input: "2 hours 30 mins", expected: "2 h 30 min", func: "shortenTime", description: "hours + mins" },
  { input: "3hr", expected: "3 h", func: "shortenTime", description: "hr to h with space" },
  { input: "1 hr 20 mins", expected: "1 h 20 min", func: "shortenTime", description: "hr to h, mins to min" },
  { input: "45 min", expected: "45 min", func: "shortenTime", description: "already min (unchanged)" },
  { input: "2h 15 min", expected: "2 h 15 min", func: "shortenTime", description: "h without space gets space added" },
  { input: "3hours 45mins", expected: "3 h 45 min", func: "shortenTime", description: "no spaces between words" },
  { input: "--", expected: "--", func: "shortenTime", description: "placeholder unchanged" },
  { input: "", expected: "", func: "shortenTime", description: "empty string unchanged" },
  { input: null, expected: null, func: "shortenTime", description: "null unchanged" },
];

// Run tests
console.log("============================================================");
console.log("Testing Time Formatting Functions");
console.log("============================================================\n");

let passed = 0;
let failed = 0;

testCases.forEach((testCase, index) => {
  const { input, expected, func, description } = testCase;
  const fn = func === "fmtDuration" ? fmtDuration : shortenTime;
  const result = fn(input);
  
  const isPass = result === expected;
  if (isPass) {
    passed++;
    console.log(`✓ Test ${index + 1}: ${description}`);
    console.log(`  Input: "${input}" => Output: "${result}"\n`);
  } else {
    failed++;
    console.log(`✗ Test ${index + 1} FAILED: ${description}`);
    console.log(`  Input: "${input}"`);
    console.log(`  Expected: "${expected}"`);
    console.log(`  Got: "${result}"\n`);
  }
});

// Integration tests - combining both functions
console.log("------------------------------------------------------------");
console.log("Integration Tests");
console.log("------------------------------------------------------------\n");

const integrationTests = [
  { 
    seconds: 4500, 
    googleFormat: "1 hour 15 mins",
    description: "Backend format vs Google API format should both produce same result"
  },
  { 
    seconds: 7800, 
    googleFormat: "2 hours 10 mins",
    description: "2 hours 10 minutes"
  },
  { 
    seconds: 1800, 
    googleFormat: "30 mins",
    description: "30 minutes"
  }
];

integrationTests.forEach((test, index) => {
  const backendResult = fmtDuration(test.seconds);
  const googleResult = shortenTime(test.googleFormat);
  
  const isPass = backendResult === googleResult;
  if (isPass) {
    passed++;
    console.log(`✓ Integration Test ${index + 1}: ${test.description}`);
    console.log(`  Backend (${test.seconds}s) => "${backendResult}"`);
    console.log(`  Google ("${test.googleFormat}") => "${googleResult}"`);
    console.log(`  Match: YES\n`);
  } else {
    failed++;
    console.log(`✗ Integration Test ${index + 1} FAILED: ${test.description}`);
    console.log(`  Backend (${test.seconds}s) => "${backendResult}"`);
    console.log(`  Google ("${test.googleFormat}") => "${googleResult}"`);
    console.log(`  Match: NO\n`);
  }
});

// Summary
console.log("============================================================");
if (failed === 0) {
  console.log(`✅ ALL TESTS PASSED (${passed}/${passed + failed})`);
  console.log("============================================================");
  process.exit(0);
} else {
  console.log(`❌ SOME TESTS FAILED (${passed} passed, ${failed} failed)`);
  console.log("============================================================");
  process.exit(1);
}
