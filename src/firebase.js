import { initializeApp } from "firebase/app"
import {
  getAuth,
  GoogleAuthProvider,
} from "firebase/auth"

const firebaseConfig = {
  apiKey: "AIzaSyBohWI2Yyz66OljCwNq9H9FxgaGWGsUzc0",
  authDomain: "wind-turbine-topic.firebaseapp.com",
  projectId: "wind-turbine-topic",
  storageBucket: "wind-turbine-topic.firebasestorage.app",
  messagingSenderId: "824445959548",
  appId: "1:824445959548:web:4402f533c063f050e3f8f9",
  measurementId: "G-3NW10VNSTV",
}

const app = initializeApp(firebaseConfig)

export const auth = getAuth(app)

export const googleProvider = new GoogleAuthProvider()

googleProvider.setCustomParameters({
  prompt: "select_account",
})